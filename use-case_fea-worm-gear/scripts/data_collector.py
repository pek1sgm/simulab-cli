import json
import io
import os
import re
import zipfile
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from time import perf_counter
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
folder_path = os.getenv('FOLDER_PATH')
target_file_name = "FEM_Medina.zip"


def _is_relevant_zip(file_path, file_name):
    if not _is_inside_model_subdir(file_path):
        return False

    file_name_lower = file_name.lower()
    if file_name_lower == target_file_name.lower():
        return True

    # Zusaetzlicher Fall: Varianten sind direkt nach "model" bereits gezippt.
    return file_name_lower.endswith(".zip")


def _is_inside_model_subdir(file_path):
    normalized = os.path.normpath(file_path)
    parts = [part.lower() for part in normalized.split(os.sep)]
    return "model" in parts


def _scan_directory(path):
    matches = []
    subdirs = []

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_file(follow_symlinks=False):
                        if _is_relevant_zip(entry.path, entry.name):
                            matches.append(entry.path)
                    elif entry.is_dir(follow_symlinks=False):
                        subdirs.append(entry.path)
                except OSError:
                    # Einzelne Zugriffsfehler ueberspringen und weitersuchen.
                    continue
    except OSError:
        # Verzeichnis nicht lesbar.
        return [], []

    return matches, subdirs


_CAE_PATTERN = re.compile(r"(CAE\d{6})")


def _parse_path(file_path):
    cae_match = _CAE_PATTERN.search(file_path)
    if not cae_match:
        return None, None
    cae_key = cae_match.group(1)

    model_marker = os.sep + "model" + os.sep
    path_lower = file_path.lower()
    model_idx = path_lower.find(model_marker.lower())
    if model_idx == -1:
        return cae_key, None

    variant_start = model_idx + len(model_marker)
    tail = file_path[variant_start:]
    tail_lower = tail.lower()

    fem_zip_suffix = os.sep + target_file_name
    fem_dir_suffix = os.sep + "FEM_Medina"

    if tail_lower.endswith(fem_zip_suffix.lower()):
        variant = tail[: -len(fem_zip_suffix)]
    elif tail_lower.endswith(fem_dir_suffix.lower()):
        variant = tail[: -len(fem_dir_suffix)]
    elif tail_lower.endswith(".zip"):
        variant = os.path.splitext(tail)[0]
    else:
        variant = tail

    variant = variant.strip("\\/")
    if not variant:
        return cae_key, None

    return cae_key, variant


def _extract_first_json_from_zip_obj(zf, max_depth, depth):
    json_entries = [
        name for name in zf.namelist()
        if name.lower().endswith(".json")
    ]
    if json_entries:
        with zf.open(json_entries[0]) as jf:
            raw = jf.read()
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return json.loads(raw.decode(enc))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return None

    if depth >= max_depth:
        return None

    nested_zip_entries = [
        name for name in zf.namelist() if name.lower().endswith(".zip")
    ]
    nested_zip_entries.sort(
        key=lambda n: ("fem_medina.zip" not in n.lower(), n.lower())
    )

    for nested_name in nested_zip_entries:
        try:
            with zf.open(nested_name) as nested_fh:
                nested_bytes = nested_fh.read()
            with zipfile.ZipFile(io.BytesIO(nested_bytes), "r") as nested_zf:
                nested_json = _extract_first_json_from_zip_obj(
                    nested_zf,
                    max_depth=max_depth,
                    depth=depth + 1,
                )
            if nested_json is not None:
                return nested_json
        except (OSError, zipfile.BadZipFile):
            continue

    return None


def _read_first_json_in_zip(zip_path, max_depth=4):
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            return _extract_first_json_from_zip_obj(
                zf,
                max_depth=max_depth,
                depth=0,
            )
    except (zipfile.BadZipFile, OSError, json.JSONDecodeError):
        return None


def build_dict(paths):
    result = {}
    for path in paths:
        cae_key, variant = _parse_path(path)
        if not cae_key or not variant:
            continue
        if "ergebnisse_txt" in variant.lower():
            continue
        if cae_key not in result:
            result[cae_key] = {
                "calculation_report_number": None,
                "calculation_report_download_link": None,
                "variants": [],
            }
        result[cae_key]["variants"].append(
            {
                "name": variant,
                "path": path,
                "json_content": _read_first_json_in_zip(path),
            }
        )
    return result


def _iter_variant_entries(cae_data):
    variants = cae_data.get("variants", [])

    if isinstance(variants, dict):
        for variant_name, variant_data in variants.items():
            if isinstance(variant_data, dict):
                yield {"name": variant_name, **variant_data}
        return

    if isinstance(variants, list):
        for variant_data in variants:
            if isinstance(variant_data, dict):
                yield variant_data


def list_all_cae_projects(root_path):
    projects = set()
    try:
        with os.scandir(root_path) as entries:
            for entry in entries:
                if not entry.is_dir(follow_symlinks=False):
                    continue
                match = _CAE_PATTERN.search(entry.name)
                if match:
                    projects.add(match.group(1))
    except OSError:
        return []

    return sorted(projects)


def split_projects_by_json(fem_zip_dict, all_projects):
    projects_with_json = set()

    for cae_key, cae_data in fem_zip_dict.items():
        if not isinstance(cae_data, dict):
            continue
        for variant_data in _iter_variant_entries(cae_data):
            if variant_data.get("json_content") is not None:
                projects_with_json.add(cae_key)
                break

    with_json = sorted(projects_with_json)
    without_json = sorted(set(all_projects) - projects_with_json)
    return with_json, without_json


def count_variants_by_json(fem_zip_dict):
    with_json = 0

    for cae_data in fem_zip_dict.values():
        if not isinstance(cae_data, dict):
            continue
        for variant_data in _iter_variant_entries(cae_data):
            if variant_data.get("json_content") is not None:
                with_json += 1

    return with_json


def list_files(folder_path, max_workers=16):
    found = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        pending = {executor.submit(_scan_directory, folder_path)}

        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                matches, subdirs = future.result()
                found.extend(matches)

                for subdir in subdirs:
                    pending.add(executor.submit(_scan_directory, subdir))

    return found


if __name__ == "__main__":
    start = perf_counter()
    fem_zip_list = list_files(folder_path)
    fem_zip_dict = build_dict(fem_zip_list)
    all_cae_projects = list_all_cae_projects(folder_path)
    cae_with_json, cae_without_json = split_projects_by_json(
        fem_zip_dict, all_cae_projects
    )

    base_dir = Path(__file__).resolve().parent.parent
    json_path = base_dir / "data" / "check_data.json"
    log_path = base_dir / "data" / "check_data.log"

    log_lines = []

    def log_print(message=""):
        # print(message)
        log_lines.append(message)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(fem_zip_dict, fh, indent=2, ensure_ascii=False)

    for path in fem_zip_list:
        log_print(path)

    log_print("")
    log_print("CAE-Projekte mit gefundener JSON:")
    for cae in cae_with_json:
        log_print(cae)

    log_print("")
    log_print("CAE-Projekte ohne gefundene JSON:")
    for cae in cae_without_json:
        log_print(cae)

    duration = perf_counter() - start
    cae_count = len(all_cae_projects)
    variant_with_json = count_variants_by_json(fem_zip_dict)
    log_print(
        f"Varianten mit JSON: {variant_with_json}"
        f" | CAE-Projekte gesamt: {cae_count}"
        f" | CAE-Projekte mit JSON: {len(cae_with_json)}"
        f" | CAE-Projekte ohne JSON: {len(cae_without_json)}"
        f" | Dauer: {duration:.2f}s | JSON: {json_path} | LOG: {log_path}"
    )

    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(log_lines) + "\n")
