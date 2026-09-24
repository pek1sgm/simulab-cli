import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REGISTRY = SCRIPT_DIR / "data" / "data.json"
SUPPORTED_EXTENSIONS = {".pptx", ".docx"}


def load_registry(registry_path: Path) -> list[dict]:
    with registry_path.open("r", encoding="utf-8-sig") as registry_file:
        data = json.load(registry_file)

    if not isinstance(data, list):
        raise ValueError(f"Registry must contain a JSON list: {registry_path}")
    return data


def find_result_dir(base_path: Path) -> Path | None:
    if not base_path.is_dir():
        return None

    for child in base_path.iterdir():
        if child.is_dir() and child.name.casefold() == "result":
            return child
    return None


def iter_office_files(result_dir: Path, recursive: bool) -> list[Path]:
    candidates = result_dir.rglob("*") if recursive else result_dir.glob("*")
    return sorted(
        path
        for path in candidates
        if path.is_file() and path.suffix.casefold() in SUPPORTED_EXTENSIONS
    )


def output_path_for(input_path: Path, office_files: list[Path]) -> Path:
    same_stem_count = sum(
        1
        for path in office_files
        if path.parent == input_path.parent and path.stem.casefold() == input_path.stem.casefold()
    )
    if same_stem_count > 1:
        return input_path.with_name(f"{input_path.name}.pdf")
    return input_path.with_suffix(".pdf")


def convert_with_libreoffice(input_path: Path, output_path: Path) -> None:
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if not executable:
        raise RuntimeError("LibreOffice executable not found in PATH")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_path.parent),
        str(input_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())

    produced_path = input_path.with_suffix(".pdf")
    produced_path = output_path.parent / produced_path.name
    if produced_path != output_path and produced_path.exists():
        produced_path.replace(output_path)

    if not output_path.exists():
        raise RuntimeError("LibreOffice finished without creating a PDF")


def convert_with_office(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    is_word_file = input_path.suffix.casefold() == ".docx"

    if is_word_file:
        powershell_script = """
$ErrorActionPreference = 'Stop'
$inputPath = [System.IO.Path]::GetFullPath($args[0])
$outputPath = [System.IO.Path]::GetFullPath($args[1])
$app = New-Object -ComObject 'Word.Application'
$document = $null
try {
    $app.Visible = $false
    $document = $app.Documents.Open($inputPath)
    $document.SaveAs($outputPath, 17)
}
finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $app) { $app.Quit() }
}
""".strip()
    else:
        powershell_script = """
$ErrorActionPreference = 'Stop'
$inputPath = [System.IO.Path]::GetFullPath($args[0])
$outputPath = [System.IO.Path]::GetFullPath($args[1])
$app = New-Object -ComObject 'PowerPoint.Application'
$presentation = $null
try {
    $presentation = $app.Presentations.Open($inputPath, 1, 0, 0)
    $presentation.SaveAs($outputPath, 32)
}
finally {
    if ($null -ne $presentation) { $presentation.Close() }
    if ($null -ne $app) { $app.Quit() }
}
""".strip()

    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as script_file:
        script_file.write(powershell_script)
        script_path = Path(script_file.name)

    try:
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            str(input_path),
            str(output_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip())
    finally:
        script_path.unlink(missing_ok=True)

    if not output_path.exists():
        raise RuntimeError("Office finished without creating a PDF")


def convert_file(input_path: Path, output_path: Path, engine: str) -> Path:
    if engine == "libreoffice":
        convert_with_libreoffice(input_path, output_path)
    else:
        convert_with_office(input_path, output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert PPTX and DOCX files from result folders listed in data.json to PDF."
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to data.json")
    parser.add_argument("--engine", choices=("office", "libreoffice"), default="office")
    parser.add_argument("--recursive", action="store_true", help="Search files recursively inside each result folder")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PDF files")
    parser.add_argument("--dry-run", action="store_true", help="Only list files that would be converted")
    args = parser.parse_args()

    registry = load_registry(args.registry)
    converted = 0
    skipped = 0
    failed = 0

    for entry in registry:
        base_path_value = entry.get("path")
        if not base_path_value:
            skipped += 1
            continue

        result_dir = find_result_dir(Path(base_path_value))
        if result_dir is None:
            print(f"SKIP no result folder: {base_path_value}")
            skipped += 1
            continue

        office_files = iter_office_files(result_dir, args.recursive)
        if not office_files:
            print(f"SKIP no pptx/docx files: {result_dir}")
            skipped += 1
            continue

        for input_path in office_files:
            output_path = output_path_for(input_path, office_files)
            if output_path.exists() and not args.overwrite:
                print(f"SKIP exists: {output_path}")
                skipped += 1
                continue

            if args.dry_run:
                print(f"WOULD CONVERT: {input_path} -> {output_path}")
                converted += 1
                continue

            try:
                created_pdf = convert_file(input_path, output_path, args.engine)
            except Exception as error:
                print(f"FAIL {input_path}: {error}", file=sys.stderr)
                failed += 1
            else:
                print(f"OK {input_path} -> {created_pdf}")
                converted += 1

    print(f"Done. converted={converted}, skipped={skipped}, failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())