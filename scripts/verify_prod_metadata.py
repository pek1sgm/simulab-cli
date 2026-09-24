"""Read-only-Vorabcheck fuer den PROD-Bulk-Upload (bulk_upload.py).

Prueft OHNE jeden Schreibzugriff, ob der PROD-Upload durchlaufen wuerde:

1. Eingabedatei (offline): Anzahl Eintraege, abgeleitete PROD-Item-Namen
   (Laenge <= 100, keine Duplikate), fehlende Varianten und fehlende
   Report-Links.
2. Metadaten (online, PROD): die in bulk_upload.build_metadata() erzeugten
   Model-/Result-Metadaten werden durch DENSELBEN Pydantic-Validator geschickt
   wie beim echten Upload (SdmManagementInputParams). Damit wird gegen die
   PROD-`selectable-values` geprueft (groupId, status, product, productType,
   simulationDomain, simulationTool).
3. Relationen (online, PROD): connectionType und sourceSystem werden durch
   dieselben Bibliotheks-Validatoren geprueft wie beim echten create_relation
   (gegen die PROD-`predefined-values`).

Es werden ausschliesslich lesende GET-Requests an simuLAB PROD gesendet. Beim
ersten Zugriff kann sich der uebliche Browser-Login oeffnen. Das Skript legt
KEIN Item an und aendert nichts.

Aufruf:  python scripts/verify_prod_metadata.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from simulabcli._instance import API_URLS, PROD, set_instance
from simulabcli._item_schema import SdmManagementInputParams, get_selectable_values
from simulabcli._utils import (
    _validate_external_system,  # bewusst: identische Validierung wie im echten create_relation
    get_predefined_values,
    validate_connection_type,
)

import bulk_upload

INPUT_FILE = (
    REPO_ROOT
    / "use-case_fea-worm-gear"
    / "data"
    / "check_data_with_reports_and_links.json"
)

# Muss mit den externen Relationen in bulk_upload.main() uebereinstimmen
# (connectionType, sourceSystem):
EXTERNAL_RELATIONS = [
    ("isBasedOnSimulationOrder", "CAE-DB"),
    ("hasSimulationReport", "Windchill (PDMLink) / Creo"),
]


def check_input_file(errors):
    print("[1/3] Eingabedatei (offline) ...")
    if not INPUT_FILE.exists():
        errors.append(f"Eingabedatei nicht gefunden: {INPUT_FILE}")
        print(f"      [FAIL] Datei fehlt: {INPUT_FILE}")
        return

    import json

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    names = []
    without_variants = []
    without_report = []
    for cae_number, entry in data.items():
        variants = entry.get("variants") or []
        if not variants:
            without_variants.append(cae_number)
            continue
        folder_name, _, _ = bulk_upload.derive_cae_folder(variants[0]["path"])
        names.append(bulk_upload.build_item_name(folder_name, PROD, 0))
        if not entry.get("calculation_report_download_link"):
            without_report.append(cae_number)

    too_long = [n for n in names if len(n) > 100]
    duplicates = sorted({n for n in names if names.count(n) > 1})

    print(f"      Eintraege gesamt:        {len(data)}")
    print(f"      davon mit Varianten:     {len(names)}")
    print(f"      max. Namenslaenge:       {max((len(n) for n in names), default=0)} (Limit 100)")
    print(f"      ohne Report-Link:        {len(without_report)} (Report-Relation wird uebersprungen)")

    if without_variants:
        # kein harter Fehler: diese CAE-Nummern werden beim Upload uebersprungen (kein Item)
        print(f"      [WARN] ohne Varianten (werden uebersprungen): {without_variants}")
    if too_long:
        errors.append(f"Item-Namen > 100 Zeichen: {too_long}")
        print(f"      [FAIL] Namen zu lang: {too_long}")
    if duplicates:
        errors.append(f"Doppelte Item-Namen: {duplicates}")
        print(f"      [FAIL] doppelte Namen: {duplicates}")
    if not too_long and not duplicates:
        print("      [OK]   Namen eindeutig und innerhalb der Laengengrenze")


def check_metadata(errors):
    print("[2/3] Metadaten gegen PROD selectable-values ...")
    for item_type in ("model", "result"):
        metadata = bulk_upload.build_metadata(
            item_type, "CAE000000", f"verify_dummy_{item_type}", PROD
        )
        try:
            # identischer Validierungspfad wie beim echten Create-Upload
            SdmManagementInputParams.from_file_or_dict_or_object(
                metadata, access_token=None
            )
            print(f"      [OK]   {item_type}: alle Metadatenwerte auf PROD gueltig")
        except Exception as exc:  # ValueError bei ungueltigem Wert
            errors.append(f"Metadaten ({item_type}) auf PROD ungueltig: {exc}")
            print(f"      [FAIL] {item_type}: {exc}")


def check_relations(errors):
    print("[3/3] Relationen gegen PROD predefined-values ...")
    internal_ct = bulk_upload.build_internal_relation_payload(
        {"sdm_number": None, "sdm_revision": None},
        {"sdm_number": None, "sdm_revision": None},
    )["connection_type"]

    connection_types = [ct for ct, _ in EXTERNAL_RELATIONS] + [internal_ct]
    for ct in connection_types:
        try:
            validate_connection_type(ct, access_token=None)
            print(f"      [OK]   connectionType '{ct}'")
        except Exception as exc:
            errors.append(f"connectionType '{ct}' auf PROD ungueltig: {exc}")
            print(f"      [FAIL] connectionType '{ct}': {exc}")

    for _, external_system in EXTERNAL_RELATIONS:
        try:
            _validate_external_system(external_system, access_token=None)
            print(f"      [OK]   sourceSystem '{external_system}'")
        except Exception as exc:
            errors.append(f"sourceSystem '{external_system}' auf PROD ungueltig: {exc}")
            print(f"      [FAIL] sourceSystem '{external_system}': {exc}")


def print_prod_reference():
    print("PROD-Referenz (zur Sichtpruefung):")
    try:
        sv = get_selectable_values(None)
        pv = get_predefined_values(None)
        tools = sv.get("simulationTool", {})
        print(f"      groupId:        {sv.get('groupId')}")
        print(f"      status:         {sv.get('status')}")
        print(f"      product:        {sv.get('product')}")
        print(f"      productType:    {sv.get('productType')}")
        print(f"      simulationTool: {sorted(tools) if hasattr(tools, '__iter__') else tools}")
        print(f"      connectionType: {pv.get('connectionType')}")
        print(f"      sourceSystem:   {pv.get('sourceSystem')}")
    except Exception as exc:
        print(f"      [WARN] Referenzwerte konnten nicht geladen werden: {exc}")


def main():
    set_instance(PROD)
    print("=" * 60)
    print(" PROD-Vorabcheck fuer bulk_upload.py  (READ-ONLY)")
    print("=" * 60)
    print(f"Zielinstanz : {PROD}  ->  {API_URLS[PROD]}")
    print("Hinweis     : Nur lesende GET-Requests. Beim ersten Zugriff kann")
    print("              sich ein Browser-Login oeffnen. Es wird nichts angelegt.")
    print("-" * 60)

    errors = []
    check_input_file(errors)
    check_metadata(errors)
    check_relations(errors)
    print("-" * 60)
    print_prod_reference()

    print("=" * 60)
    if errors:
        print(f" ERGEBNIS: NO-GO  ({len(errors)} Problem(e))")
        for err in errors:
            print(f"   - {err}")
        print("=" * 60)
        sys.exit(1)
    print(" ERGEBNIS: GO  -  Metadaten und Relationen sind auf PROD gueltig.")
    print("=" * 60)


if __name__ == "__main__":
    main()
