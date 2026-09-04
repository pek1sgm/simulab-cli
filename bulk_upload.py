"""Bulk-Upload von Model- und Result-Items nach simuLAB.

M3: Metadata-Aufbau & Registry-Helper inkl. pls_delete_<idx>_ Namenspraefix.
M4: Relation-Payload-Aufbau (nur Dateien, kein API-Call).
M5: echter Upload (Create-Pfad) ueber simulabcli.cli.upload_directory().
M7: Relations-Ausfuehrung ueber simulabcli.cli.create_relation().
M8: Abschluss-Summary (neu/aktualisiert/uebersprungen).
M9: gezielter Upload einzelner CAE-Nummern via --cae-numbers.
"""

import argparse
import json
import logging
import re
import shutil
from pathlib import Path

import simulabcli.cli
from simulabcli._instance import set_instance

# unterdrueckt das (harmlose) 404-Error-Log des internen Lock-Checks (kein Lock vorhanden)
logging.getLogger("simulabcli._requests").setLevel(logging.CRITICAL)

DEFAULT_INPUT = Path(
    "use-case_fea-worm-gear/scripts/check_data_with_reports_and_links.json"
)
DEFAULT_TEMP_DIR = Path("C:/temp/simulab")
DEFAULT_REGISTRY = Path("bulk_upload_registry.json")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Pfad zur JSON-Datei mit den Varianten")
    parser.add_argument("--instance", choices=["QA", "PROD"], default="QA", help="Zielinstanz für den Upload (QA oder PROD)")
    parser.add_argument("--limit", type=int, default=None, help="Maximale Anzahl an zu verarbeitenden Einträgen")
    parser.add_argument("--dummy-data", action="store_true", help="Platzhalterdateien anlegen statt echte Dateien zu kopieren")
    parser.add_argument("--temp-dir", type=Path, default=DEFAULT_TEMP_DIR, help="Lokales Verzeichnis für vorbereitete Dateien")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Pfad zur Registry-Datei")
    parser.add_argument("--cae-numbers", nargs="+", default=None, metavar="CAE_NUMMER", help="Nur diese CAE-Nummern verarbeiten (ignoriert --limit)")
    return parser.parse_args()


def derive_cae_folder(variant_path):
    """Leitet aus einem Varianten-Pfad (.../<CAE-Ordner>/model/<datei>.zip)
    den CAE-Ordnernamen sowie die Netzlaufwerk-Pfade zu model/ und
    result/ ab."""
    parts = Path(variant_path).parts
    model_index = parts.index("model")
    cae_folder_name = parts[model_index - 1]
    base_parts = parts[:model_index]
    network_model_dir = Path(*base_parts, "model")
    network_result_dir = Path(*base_parts, "result")
    return cae_folder_name, network_model_dir, network_result_dir


def prepare_local_dir(local_dir, network_dir, dummy):
    """Legt local_dir sauber neu an (löscht vorhandenen Inhalt) und
    befüllt es entweder mit Platzhalterdateien (dummy=True) oder einer
    Kopie von network_dir. Liefert False, falls network_dir nicht
    existiert (nur relevant für dummy=False)."""
    if shutil.os.path.exists(local_dir):
        shutil.rmtree(local_dir)

    if dummy:
        local_dir.mkdir(parents=True)
        for i in range(1, 3):
            (local_dir / f"dummy_{i}.txt").write_text(
                f"Platzhalterdatei {i}", encoding="utf-8"
            )
        return True

    if not network_dir.exists():
        print(f"  [WARN] Netzlaufwerk-Ordner nicht gefunden: {network_dir}")
        return False

    shutil.copytree(network_dir, local_dir)
    return True


def write_variant_json_files(local_model_dir, variants):
    """Schreibt für jede Variante mit vorhandenem json_content eine <name>.json
    Datei nach local_model_dir (name kann Backslash-Unterordner enthalten)."""
    for variant in variants:
        json_content = variant.get("json_content")
        if json_content is None:
            continue

        name_parts = variant["name"].split("\\")
        target_path = Path(local_model_dir, *name_parts).with_suffix(".json")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)


def next_delete_index(registry):
    """Durchsucht alle in der Registry gespeicherten Namen (ueber alle
    CAE-Nummern und Instanzen, model+result) nach dem Muster
    pls_delete_(\\d+)_ und liefert den hoechsten gefundenen Wert +1 (oder 1,
    falls keiner gefunden wird)."""
    max_index = 0
    for cae_entry in registry.values():
        for instance_entry in cae_entry.values():
            for item_type in ("model", "result"):
                name = instance_entry.get(item_type, {}).get("name")
                if not name:
                    continue
                match = re.match(r"pls_delete_(\d+)_", name)
                if match:
                    max_index = max(max_index, int(match.group(1)))
    return max_index + 1


def build_item_name(folder_name, instance, index):
    """Liefert auf QA folder_name mit fortlaufendem pls_delete_<index>_
    Praefix, auf PROD unveraendert folder_name."""
    if instance == "QA":
        return f"pls_delete_{index:03d}_{folder_name}"
    return folder_name


def build_metadata(item_type, cae_number, folder_name, instance):
    """Baut das Metadata-Dict fuer ein Model- oder Result-Item nach den
    Vorgaben aus den Metadata-Vorlagen. folder_name ist bereits der fertige
    (ggf. mit pls_delete_<idx>_ praefixierte) Name. Ergaenzt auf QA den Tag
    "delete in future"."""
    if item_type == "model":
        # kein Tool noetig -> Feld bleibt leer (Aequivalent zu "nichts angeben" in der UI)
        simulation_tools = [{"toolName": "MEDINA", "toolVersion": None, "toolSource": None}, {"toolName": "PERMAS", "toolVersion": None, "toolSource": None}]
    else:
        simulation_tools = [{"toolName": "Matlab", "toolVersion": None, "toolSource": None}]

    tags = []
    if instance == "QA":
        tags.append("delete in future")

    return {
        "groupId": "vm-simulation",
        "name": folder_name,
        "type": item_type,
        "status": "In Work",
        "description": f"FEA Worm Gear Unit ({item_type})",
        "projectNumber": cae_number,
        "product": "eps",
        "productType": "steering-system (steer-by-wire)",
        "simulationDomain": ["Structural Mechanics"],
        "simulationTool": simulation_tools,
        "tags": tags,
    }


def build_update_metadata(metadata, change_description="Bulk-Update via bulk_upload.py"):
    """Leitet aus einem Create-Metadata-Dict die Update-Variante ab: ohne
    groupId/type (im Update-Schema nicht erlaubt), dafuer mit
    changeDescription."""
    update_metadata = {
        key: value for key, value in metadata.items() if key not in ("groupId", "type")
    }
    update_metadata["changeDescription"] = change_description
    return update_metadata


def build_upload_payload(directory, metadata, existing=None):
    """Baut das Parameter-Dict fuer simulabcli.cli.upload_directory() im
    gleichen Schema wie templates/upload_directory_template.json bzw.
    upload_existing_directory_template.json. Kann direkt per
    'simulabcli --instance QA -f <datei> upload_directory' verwendet
    oder spaeter per json.load(...) + upload_directory(**payload)
    aufgerufen werden."""
    payload = {"directory": str(directory), "metadata": metadata}
    if existing is not None:
        payload["existing_sdm_number"] = existing["sdm_number"]
        payload["existing_sdm_revision"] = existing["sdm_revision"]
    payload["ignore_list"] = None
    payload["access_token"] = None
    return payload


def build_external_relation_payload(connection_type, source, external_system, external_id, external_link):
    """Baut das Parameter-Dict fuer simulabcli.cli.create_relation() (externe
    Relation) im Schema von templates/create_external_relation_template.json.
    source ist ein Dict mit sdm_number/sdm_revision (noch Platzhalter None vor
    dem echten Upload in M5/M7)."""
    return {
        "connection_type": connection_type,
        "source_sdm_number": source["sdm_number"],
        "source_sdm_revision": source["sdm_revision"],
        "external_system": external_system,
        "external_id": external_id,
        "external_version": None,
        "external_link": external_link,
        "internal": False,
        "access_token": None,
    }


def build_internal_relation_payload(source, target):
    """Baut das Parameter-Dict fuer simulabcli.cli.create_relation() (interne
    Relation generatesResult) im Schema von
    templates/create_internal_relation_template.json."""
    return {
        "connection_type": "generatesResult",
        "source_sdm_number": source["sdm_number"],
        "source_sdm_revision": source["sdm_revision"],
        "target_sdm_number": target["sdm_number"],
        "target_sdm_revision": target["sdm_revision"],
        "internal": True,
        "access_token": None,
    }


def write_json_file(target_dir, filename, data):
    """Schreibt data als JSON-Datei nach target_dir/filename (auf
    gleicher Ebene wie die model/result-Ordner)."""
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def execute_relation(local_cae_dir, filename, source=None, target=None):
    """Laedt die von M4 geschriebene relation_*.json-Datei (falls vorhanden),
    ersetzt die null-Platzhalter durch die echten sdm_number/sdm_revision aus
    source/target und ruft simulabcli.cli.create_relation() auf. Ueberspringt
    sauber (Warnung), falls die Datei nicht existiert (z.B. fehlender Link)."""
    path = local_cae_dir / filename
    if not path.exists():
        print(f"  [SKIP] {filename}: Datei nicht vorhanden, Relation wird uebersprungen")
        return None

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if source is not None:
        payload["source_sdm_number"] = source["sdm_number"]
        payload["source_sdm_revision"] = source["sdm_revision"]
    if target is not None:
        payload["target_sdm_number"] = target["sdm_number"]
        payload["target_sdm_revision"] = target["sdm_revision"]

    # vor dem API-Call zurueckschreiben, damit die Datei auch bei einem Fehler als Log dient
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    simulabcli.cli.create_relation(**payload)
    print(f"  [OK] {filename}: Relation erstellt ({payload['connection_type']})")


def load_registry(path):
    """Laedt die Registry-Datei (CAE-Nummer -> sdm_number/sdm_revision je
    model/result). Liefert ein leeres Dict, falls die Datei noch nicht
    existiert."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_or_update_item(payload):
    """Ruft simulabcli.cli.upload_directory() mit dem gebauten Payload-Dict
    auf (Create oder Update, je nachdem ob existing_sdm_number gesetzt ist).
    Liefert das Ergebnis-Dict (u.a. sdm_number, sdm_revision)."""
    return simulabcli.cli.upload_directory(**payload)


def main():
    args = parse_args()
    set_instance(args.instance)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    registry = load_registry(args.registry)

    if args.cae_numbers is not None:
        entries = []
        for cae_number in args.cae_numbers:
            if cae_number not in data:
                print(f"[WARN] {cae_number}: nicht in Eingabedatei gefunden, wird uebersprungen")
                continue
            entries.append((cae_number, data[cae_number]))
    else:
        entries = list(data.items())

    count = 0
    new_count = 0
    updated_count = 0
    skipped_count = 0
    for cae_number, entry in entries:
        if args.cae_numbers is None and args.limit is not None and count >= args.limit:
            break

        variants = entry.get("variants") or []
        if not variants:
            print(f"[SKIP] {cae_number}: keine Varianten vorhanden")
            skipped_count += 1
            continue

        variant_path = variants[0]["path"]
        (
            cae_folder_name,
            network_model_dir,
            network_result_dir,
        ) = derive_cae_folder(variant_path)

        local_cae_dir = args.temp_dir / cae_folder_name
        local_model_dir = local_cae_dir / "model"
        local_result_dir = local_cae_dir / "result"

        print(f"CAE-Nummer: {cae_number}")
        print(f"  cae_folder_name:     {cae_folder_name}")
        print(f"  network_model_dir:   {network_model_dir}")
        print(f"  network_result_dir:  {network_result_dir}")
        print(f"  local_model_dir:     {local_model_dir}")
        print(f"  local_result_dir:    {local_result_dir}")

        model_ok = prepare_local_dir(
            local_model_dir, network_model_dir, args.dummy_data
        )
        if not model_ok:
            print(f"  [SKIP] {cae_number}: model-Ordner nicht vorbereitet")
            skipped_count += 1
            continue

        result_ok = prepare_local_dir(
            local_result_dir, network_result_dir, args.dummy_data
        )
        if not result_ok:
            print(f"  [SKIP] {cae_number}: result-Ordner nicht vorbereitet")
            skipped_count += 1
            continue

        write_variant_json_files(local_model_dir, variants)

        # Registry ist pro Instanz verschachtelt (registry[cae_number][instance]),
        # damit QA- und PROD-Eintraege derselben CAE-Nummer sich nicht vermischen.
        cae_registry = registry.get(cae_number, {})
        already_registered = args.instance in cae_registry

        # Auf QA sollen Testdaten immer als NEUES Item angelegt werden (auch wenn die
        # CAE-Nummer/Instanz schon in der Registry steht) - nur auf PROD ist die Registry
        # massgeblich fuer Create-vs-Update (Idempotenz, keine Duplikate).
        is_new = args.instance == "QA" or not already_registered
        existing_model = cae_registry.get(args.instance, {}).get("model") if not is_new else None
        existing_result = cae_registry.get(args.instance, {}).get("result") if not is_new else None

        if is_new:
            # Zaehler steigt innerhalb eines CAE-Eintrags von model zu result weiter.
            model_index = next_delete_index(registry)
            model_name = build_item_name(cae_folder_name, args.instance, model_index)
            result_name = build_item_name(cae_folder_name, args.instance, model_index + 1)
        else:
            model_name = existing_model["name"]
            result_name = existing_result["name"]

        model_metadata = build_metadata("model", cae_number, model_name, args.instance)
        result_metadata = build_metadata("result", cae_number, result_name, args.instance)

        if not is_new:
            model_metadata = build_update_metadata(model_metadata)
            result_metadata = build_update_metadata(result_metadata)

        model_payload = build_upload_payload(local_model_dir, model_metadata, existing_model)
        result_payload = build_upload_payload(local_result_dir, result_metadata, existing_result)

        mode = "create" if is_new else "update"
        print(f"  upload payload (model, {mode}):")
        print(json.dumps(model_payload, indent=2, ensure_ascii=False))
        print(f"  upload payload (result, {mode}):")
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))

        write_json_file(local_cae_dir, "model_upload_directory.json", model_payload)
        write_json_file(local_cae_dir, "result_upload_directory.json", result_payload)

        model_result = create_or_update_item(model_payload)
        result_result = create_or_update_item(result_payload)
        print(f"  model sdm_number:  {model_result['sdm_number']} (revision {model_result['sdm_revision']})")
        print(f"  result sdm_number: {result_result['sdm_number']} (revision {result_result['sdm_revision']})")

        # Registry sofort nach jedem Upload speichern (crash-sicher).
        registry.setdefault(cae_number, {})[args.instance] = {
            "model": {
                "name": model_name,
                "sdm_number": model_result["sdm_number"],
                "sdm_revision": model_result["sdm_revision"],
            },
            "result": {
                "name": result_name,
                "sdm_number": result_result["sdm_number"],
                "sdm_revision": result_result["sdm_revision"],
            },
        }
        save_registry(args.registry, registry)

        if is_new:
            new_count += 1
        else:
            updated_count += 1

        if is_new:
            # echte sdm_number/sdm_revision existieren noch nicht (Upload folgt erst in M5) ->
            # Platzhalter, werden in M7 durch die echten Werte ersetzt.
            model_placeholder = {"sdm_number": None, "sdm_revision": None}
            result_placeholder = {"sdm_number": None, "sdm_revision": None}

            caedb_url = entry.get("caedb_url")
            if caedb_url:
                relation_external_model = build_external_relation_payload(
                    "isBasedOnSimulationOrder", model_placeholder, "CAE-DB", cae_number, caedb_url
                )
                write_json_file(local_cae_dir, "relation_external_model.json", relation_external_model)
                execute_relation(local_cae_dir, "relation_external_model.json", source=model_result)
            else:
                print(f"  [WARN] {cae_number}: kein caedb_url vorhanden, relation_external_model.json wird uebersprungen")

            report_link = entry.get("calculation_report_download_link")
            if report_link:
                relation_external_result = build_external_relation_payload(
                    "hasSimulationReport", result_placeholder, "Windchill (PDMLink) / Creo", cae_number, report_link
                )
                write_json_file(local_cae_dir, "relation_external_result.json", relation_external_result)
                execute_relation(local_cae_dir, "relation_external_result.json", source=result_result)
            else:
                print(f"  [WARN] {cae_number}: kein calculation_report_download_link vorhanden, relation_external_result.json wird uebersprungen")

            # source=model, target=result (generatesResult: das Model-Item erzeugt das Result-Item)
            relation_internal = build_internal_relation_payload(model_placeholder, result_placeholder)
            write_json_file(local_cae_dir, "relation_internal_model_result.json", relation_internal)
            execute_relation(
                local_cae_dir, "relation_internal_model_result.json", source=model_result, target=result_result
            )

        count += 1

    save_registry(args.registry, registry)

    print("\n=== Summary ===")
    print(f"  neu:          {new_count}")
    print(f"  aktualisiert: {updated_count}")
    print(f"  uebersprungen:{skipped_count}")


if __name__ == "__main__":
    main()
