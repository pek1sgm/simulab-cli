"""Bulk-Upload von Result-Items nach simuLAB.
Use Case: FEA Metal & Plastic Components.
"""

import argparse
import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

import simulabcli.cli
from simulabcli._instance import set_instance

# unterdrueckt das (harmlose) 404-Error-Log des internen Lock-Checks (kein Lock vorhanden)
logging.getLogger("simulabcli._requests").setLevel(logging.CRITICAL)

DEFAULT_INPUT = Path(
    "use-case_fea-met-plast-comp/data/data_registry.json"
)
DEFAULT_TEMP_DIR = Path("C:/temp/simulab")
DEFAULT_REGISTRY = Path(__file__).resolve().parent / "use-case_fea-met-plast-comp" / "data" / "bulk_upload_registry.json"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Pfad zur JSON-Datei (Liste) mit den Eintraegen")
    parser.add_argument("--instance", choices=["QA", "PROD"], default="QA", help="Zielinstanz für den Upload (QA oder PROD)")
    parser.add_argument("--limit", type=int, default=None, help="Maximale Anzahl an zu verarbeitenden Einträgen")
    parser.add_argument("--dummy-data", action="store_true", help="Platzhalterdateien anlegen statt echte Dateien zu kopieren")
    parser.add_argument("--temp-dir", type=Path, default=DEFAULT_TEMP_DIR, help="Lokales Verzeichnis für vorbereitete Dateien")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Pfad zur Registry-Datei")
    parser.add_argument("--cae-numbers", nargs="+", default=None, metavar="CAE_NUMMER", help="Nur diese CAE-Nummern verarbeiten (ignoriert --limit)")
    parser.add_argument("--description", default="FEA Metal & Plastic Components", help="Beschreibungstext fuer die Metadata")
    parser.add_argument("--simulation-tool", nargs="+", default=["Abaqus"], metavar="TOOL", help="Simulationstools fuer das result-Item")
    parser.add_argument("--simulation-domain", nargs="+", default=["Structural Mechanics"], metavar="DOMAIN", help="Simulationsdomaenen fuer die Metadata")
    return parser.parse_args()


def prepare_local_dir(local_dir, network_dir, dummy):
    """Befuellt local_dir mit Platzhalterdateien (dummy=True) oder kopiert die
    Dateien aus network_dir. Es werden nur Dateien geladen, die lokal noch
    nicht vorhanden sind (kein Ueberschreiben). Liefert False, falls
    network_dir nicht existiert (nur relevant fuer dummy=False)."""
    if dummy:
        local_dir.mkdir(parents=True, exist_ok=True)
        for i in range(1, 3):
            target = local_dir / f"dummy_{i}.txt"
            if not target.exists():
                target.write_text(f"Platzhalterdatei {i}", encoding="utf-8")
        return True

    if not network_dir.exists():
        print(f"  [WARN] Netzlaufwerk-Ordner nicht gefunden: {network_dir}")
        return False

    local_dir.mkdir(parents=True, exist_ok=True)
    for source in network_dir.rglob("*"):
        target = local_dir / source.relative_to(network_dir)
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return True


def next_delete_index(registry):
    """Durchsucht alle in der Registry gespeicherten result-Namen nach dem
    Muster pls_delete_(\\d+)_ und liefert den hoechsten gefundenen Wert +1
    (oder 1, falls keiner gefunden wird)."""
    max_index = 0
    for cae_entry in registry.values():
        for instance_entry in cae_entry.values():
            name = instance_entry.get("result", {}).get("name")
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


def build_metadata(cae_number, folder_name, instance, description, simulation_tool_names, simulation_domain):
    """Baut das Metadata-Dict fuer ein result-Item nach den Vorgaben aus den
    Metadata-Vorlagen. folder_name ist bereits der fertige (ggf. mit
    pls_delete_<idx>_ praefixierte) Name. Ergaenzt auf QA den Tag
    "delete in future"."""
    simulation_tools = [{"toolName": name, "toolVersion": None, "toolSource": None} for name in simulation_tool_names]

    tags = []
    if instance == "QA":
        tags.append("delete in future")

    return {
        "groupId": "vm-simulation",
        "name": folder_name,
        "type": "result",
        "status": "In Work",
        "description": f"{description}",
        "projectNumber": cae_number,
        "product": "eps",
        "productType": "steering-system (steer-by-wire)",
        "simulationDomain": simulation_domain,
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


def write_json_file(target_dir, filename, data):
    """Schreibt data als JSON-Datei nach target_dir/filename (auf
    gleicher Ebene wie der result-Ordner)."""
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
    """--input ist eine Liste (wie data_registry.json) mit cae-no./path/cae_url/
    calculation_report_number/download_link je Eintrag. Legt pro Eintrag ein
    result-Item an (Daten werden vollstaendig inkl. Unterverzeichnisse aus
    path kopiert) und verknuepft es per externer Relation mit der CAE-DB-
    Aufgabe sowie (falls vorhanden) dem technischen Bericht."""
    args = parse_args()
    set_instance(args.instance)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    registry = load_registry(args.registry)

    if args.cae_numbers is not None:
        entries = [entry for entry in data if entry["cae-no."] in args.cae_numbers]
        found = {entry["cae-no."] for entry in entries}
        for cae_number in args.cae_numbers:
            if cae_number not in found:
                print(f"[WARN] {cae_number}: nicht in Eingabedatei gefunden, wird uebersprungen")
    else:
        entries = data

    count = 0
    new_count = 0
    updated_count = 0
    skipped_count = 0
    for entry in entries:
        cae_number = entry["cae-no."]
        if args.cae_numbers is None and args.limit is not None and count >= args.limit:
            break

        network_dir = Path(entry["path"])
        cae_folder_name = network_dir.name

        local_cae_dir = args.temp_dir / cae_folder_name
        local_result_dir = local_cae_dir / "result"

        print(f"CAE-Nummer: {cae_number}")
        print(f"  network_dir:         {network_dir}")
        print(f"  local_result_dir:    {local_result_dir}")

        result_ok = prepare_local_dir(local_result_dir, network_dir, args.dummy_data)
        if not result_ok:
            print(f"  [SKIP] {cae_number}: result-Ordner nicht vorbereitet")
            skipped_count += 1
            continue

        # Registry ist pro Instanz verschachtelt (registry[cae_number][instance]),
        # damit QA- und PROD-Eintraege derselben CAE-Nummer sich nicht vermischen.
        cae_registry = registry.get(cae_number, {})
        already_registered = args.instance in cae_registry

        # Auf QA sollen Testdaten immer als NEUES Item angelegt werden (auch wenn die
        # CAE-Nummer/Instanz schon in der Registry steht) - nur auf PROD ist die Registry
        # massgeblich fuer Create-vs-Update (Idempotenz, keine Duplikate).
        is_new = args.instance == "QA" or not already_registered
        existing_result = cae_registry.get(args.instance, {}).get("result") if not is_new else None

        if is_new:
            result_index = next_delete_index(registry)
            result_name = build_item_name(cae_folder_name, args.instance, result_index)
        else:
            result_name = existing_result["name"]

        result_metadata = build_metadata(
            cae_number, result_name, args.instance,
            args.description, args.simulation_tool, args.simulation_domain,
        )
        if not is_new:
            result_metadata = build_update_metadata(result_metadata)

        result_payload = build_upload_payload(local_result_dir, result_metadata, existing_result)

        mode = "create" if is_new else "update"
        print(f"  upload payload (result, {mode}):")
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))

        write_json_file(local_cae_dir, "result_upload_directory.json", result_payload)

        result_result = create_or_update_item(result_payload)
        print(f"  result sdm_number: {result_result['sdm_number']} (revision {result_result['sdm_revision']})")

        # Registry sofort nach jedem Upload speichern (crash-sicher).
        registry.setdefault(cae_number, {})[args.instance] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
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
            # echte sdm_number/sdm_revision existieren noch nicht vor dem Upload ->
            # Platzhalter, werden in execute_relation() durch die echten Werte ersetzt.
            result_placeholder = {"sdm_number": None, "sdm_revision": None}

            cae_url = entry.get("cae_url")
            if cae_url:
                relation_external_cae = build_external_relation_payload(
                    "isBasedOnSimulationOrder", result_placeholder, "CAE-DB", cae_number, cae_url
                )
                write_json_file(local_cae_dir, "relation_external_result_cae.json", relation_external_cae)
                execute_relation(local_cae_dir, "relation_external_result_cae.json", source=result_result)
            else:
                print(f"  [WARN] {cae_number}: kein cae_url vorhanden, relation_external_result_cae.json wird uebersprungen")

            download_link = entry.get("download_link")
            if download_link:
                relation_external_report = build_external_relation_payload(
                    "hasSimulationReport", result_placeholder, "Windchill (PDMLink) / Creo", cae_number, download_link
                )
                write_json_file(local_cae_dir, "relation_external_result_report.json", relation_external_report)
                execute_relation(local_cae_dir, "relation_external_result_report.json", source=result_result)
            else:
                print(f"  [WARN] {cae_number}: kein download_link vorhanden, relation_external_result_report.json wird uebersprungen")

        count += 1

    save_registry(args.registry, registry)

    print("\n=== Summary ===")
    print(f"  neu:          {new_count}")
    print(f"  aktualisiert: {updated_count}")
    print(f"  uebersprungen:{skipped_count}")


if __name__ == "__main__":
    main()

