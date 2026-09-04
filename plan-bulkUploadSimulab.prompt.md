# Plan: bulk_upload.py – Model+Result Upload nach simuLAB

## TL;DR
Ein neues Skript `bulk_upload.py` im Projekt-Root liest `check_data_with_reports_and_links.json`,
legt pro CAE-Nummer zwei simuLAB-Items an (type "model" und type "result"), kopiert dazu die
Netzlaufwerk-Ordner `model`/`result` nach `C:\temp\simulab\<CAE-Ordner>\...` (oder erzeugt
Dummy-Dateien für QA-Tests), schreibt dazu fertige `upload_directory`-Parameter-Dateien
(`model_upload_directory.json`/`result_upload_directory.json`, gleiches Schema wie die
simulabcli-Templates) neben die model/result-Ordner, ruft `simulabcli` direkt als
Python-Funktionen auf (`upload_directory(**payload)`, `create_relation`), und merkt sich
angelegte SDM-Nummern in einer lokalen JSON-Registry, um bei Re-Runs zu updaten statt zu
duplizieren.

## Entscheidungen aus Rückfragen
- Model-Item: Inhalt von `<CAE-Ordner>\model` hochladen. Result-Item: Inhalt von
  `<CAE-Ordner>\result` (Geschwisterordner, existiert laut User real).
- Re-Runs: lokale Registry-Datei `bulk_upload_registry.json` (Projekt-Root) merkt sich pro
  CAE-Nummer die sdm_number/sdm_revision von model+result → beim nächsten Lauf Update statt
  Neuanlage (`upload_directory` mit `existing_sdm_number`/`existing_sdm_revision`).
- Skriptname: `bulk_upload.py` (neu, `main.py` bleibt unangetastet).
- Dummy-Daten (QA-Test): 1-2 generierte Platzhalter-Textdateien statt echter Netzlaufwerk-Kopie.
- `--instance` CLI-Parameter, Default `QA`.
- Aufruf-Art: simulabcli-Funktionen direkt importieren/aufrufen (kein subprocess/CLI-Parsing).
  Parameter-Dict wird trotzdem 1:1 nach dem Schema der Templates gebaut (Nachvollziehbarkeit).
- Zusätzlich zum reinen Metadata-Dict wird pro model/result ein komplettes
  `upload_directory`-Parameter-Dict (`directory`, `metadata`, ggf. `existing_sdm_number`/
  `existing_sdm_revision`, `ignore_list`, `access_token`) als JSON-Datei neben den jeweiligen
  model/result-Ordner geschrieben (`model_upload_directory.json`/`result_upload_directory.json`).
  Damit ist derselbe Aufruf sowohl manuell über `simulabcli --instance QA -f <datei>
  upload_directory` als auch später im Skript per `upload_directory(**payload)` nutzbar.
- Relations (2x external + 1x internal) werden NUR beim erstmaligen Anlegen einer CAE-Nummer
  erzeugt (is_new = CAE-Nummer noch nicht in Registry), nicht bei Updates. Zweistufig wie beim
  Upload: zuerst nur die `create_relation`-Parameter-Dateien (JSON) neben
  `model_upload_directory.json`/`result_upload_directory.json` ablegen (M4), der echte
  `create_relation`-Call folgt erst in einer späteren Milestone (M7).
- Alle Items, die auf der QA-Instanz (`--instance QA`) angelegt/aktualisiert werden, erhalten
  zusätzlich den generellen Metadaten-Tag `"delete in future"` im `tags`-Feld, damit sie später
  klar als Testdaten zum Löschen erkennbar sind. Auf PROD wird dieser Tag NICHT gesetzt.
- Zusätzlich erhält der SDM-Name auf QA einen fortlaufenden Präfix `pls_delete_<idx>_` vor dem
  bisherigen Namen (`folder-with-CAE-No`), z.B. `pls_delete_001_CAE018147_RunIn_Geometry_Symmetry`.
  `idx` ist ein einfach hochzählender Integer (3-stellig, zero-padded), der vorab aus dem
  Upload-Index (Registry) ermittelt wird: höchsten bereits vergebenen `pls_delete_<idx>_`-Wert
  über alle Namen in der Registry suchen, +1 verwenden (Registry leer/kein Treffer → `001`).
  Bei Updates wird der beim Erstanlegen vergebene Name aus der Registry wiederverwendet (kein
  neuer Index). Auf PROD entfällt dieser Präfix. Betrifft `build_metadata` (M3).

## Kontext aus Recherche
- Quelldatei `use-case_fea-worm-gear/scripts/check_data_with_reports_and_links.json`: Dict
  keyed by CAE-Nummer (z.B. `"CAE018147"`), Felder: `calculation_report_number` (str|null),
  `calculation_report_download_link` (str|null), `caedb_url` (str, optional/fehlt manchmal),
  `variants`: Liste von `{name, path, json_content}`. `path` ist UNC-Pfad zu einer .zip Datei
  unterhalb von `<CAE-Ordner>\model\`. Der Ordnername (`folder-with-CAE-No`, z.B.
  `CAE018147_RunIn_Geometry_Symmetry`) muss aus `path` extrahiert werden (Segment vor `\model\`).
  Der `result`-Geschwisterordner liegt auf gleicher Ebene wie `model`.
- `simulabcli.cli.upload_directory(directory, metadata, existing_sdm_number=None,
  existing_sdm_revision=None, ignore_list=None, access_token=None)` – deckt Create UND Update
  ab (übernimmt selbst files-listing, ignoriert automatisch `*.key`/`*-protokoll.txt`). Wirft
  `ValueError` bei ungültigem/leerem Verzeichnis.
- Rückgabe (`model_dump()`, KEIN `by_alias`) → **snake_case Keys**: `message`, `sdm_number`,
  `sdm_revision`, `sdm_version`, `simulation_box_id`.
- `simulabcli.cli.create_relation(connection_type, source_sdm_number, source_sdm_revision,
  target_sdm_number=None, target_sdm_revision=None, external_system=None, external_id=None,
  external_version=None, external_link=None, internal=True/False, access_token=None)`.
- Metadata-Dict-Schema (`SdmManagementInputParams`, `extra="forbid"`!): Pflicht `groupId`,
  `name` (≤100 Zeichen), `type` ("model"|"result"). Optional: `status` (default "In Work"),
  `description`, `projectNumber`, `product`, `productType`, `simulationDomain` (**Liste** von
  str), `simulationTool` (**Liste** von `{toolName, toolVersion, toolSource}`), `tags` (Liste).
  **WICHTIG:** Für Update (`SdmManagementUpdateParams`) gibt es KEINE Felder `groupId`/`type`
  (nur in `SdmManagementInputParams`) – beim Update-Call dürfen diese beiden Keys NICHT im
  Metadata-Dict enthalten sein, sonst Pydantic-Fehler wegen `extra="forbid"`. Stattdessen dort
  `changeDescription` (Pflicht laut Doku-Warnung, str) ergänzen.
- Alle Metadata-Werte (`groupId`, `product`, `productType`, `simulationDomain`,
  `simulationTool.toolName`) werden bei jedem Call **live gegen die API** validiert
  (`get_selectable_values`) – Tippfehler/unbekannte Werte führen zur Laufzeit zu Fehlern (kein
  Vorab-Check im Skript nötig/vorgesehen, passt zu "nicht überkonstruiert").
- **Verifiziert per echtem CLI-Call** (`simulabcli --instance QA -f ... upload_directory`):
  `simulationTool.toolName: "-"` ist **kein gültiger Wert** (`SimulationTool.check_name_version`
  prüft `toolName` immer gegen `get_selectable_values()["simulationTool"]`, unabhängig vom
  generischen `extra="forbid"`-Schutz). Da das Model-Item laut User-Vorgabe kein echtes Tool
  braucht ("in der UI muss man nix angeben"), wird `simulationTool` dort auf `null` gesetzt
  (Äquivalent zum leeren UI-Feld) statt eines Platzhalter-Tools. Für das Result-Item bleibt
  `toolName: "Matlab"` (gültig), `toolVersion`/`toolSource` werden ebenfalls auf `null` gesetzt
  (statt `"-"`), da eine erfundene Version/Quelle ebenfalls an der Live-Validierung scheitern
  könnte.
- Instanz-Steuerung: `from simulabcli._instance import set_instance; set_instance("QA"|"PROD")`
  einmalig zu Beginn (so macht es auch `simulabcli.cli.main()` selbst).
- `docs/MongoDB-data-models.md`: `type` fix `"model"|"result"`, `status` `"In Work"|"Release"`.
  Connection-Types wie `isBasedOnSimulationOrder`/`hasSimulationReport` sind nicht in den
  beiden Docs gelistet (nur dynamisch über API abrufbar) – werden aber laut User-Vorgabe direkt
  übernommen, API validiert zur Laufzeit.
- Bestehender Code-Stil (`use-case_fea-worm-gear/scripts/*.py`): rein funktional (keine
  Klassen), `print()`-Logging, defensives try/except pro Objekt (nicht global), JSON mit
  `ensure_ascii=False`, `pathlib.Path` bevorzugt. Neues Skript soll diesem Stil folgen –
  **kein** argparse-Overkill, aber CLI-Flags sind explizit vom User gewünscht (siehe unten).
- Kein Delete-Endpunkt in der simuLAB-API vorhanden (nur `isDeleted`-Feld im MongoDB-Schema,
  seit 2026-08-26, ohne zugehörigen dokumentierten REST-Endpunkt) → Grund für die
  `"delete in future"`-Tag-Konvention auf QA statt echtem Löschen.

## Metadata-Vorlagen (aus User-Vorgabe, wörtlich übernehmen)

**Model-Item:**
```
groupId: vm-simulation
name: <folder-with-CAE-No>  # auf QA mit Präfix pls_delete_<idx>_ (siehe Entscheidungen)
type: model
status: In Work
description: FEA Worm Gear Unit (model)
projectNumber: <CAE-Nummer>
product: eps
productType: steering-system (steer-by-wire)
simulationDomain: [Structural Mechanics]
simulationTool: null  # kein Tool nötig (Äquivalent zu "nichts angeben" in der simuLAB-UI)
tags: []  # auf QA zusätzlich: ["delete in future"]
```
Relation (nur bei is_new): external, connection_type=isBasedOnSimulationOrder,
external_system=CAE-DB, external_id=<CAE-Nummer>, external_link=caedb_url (skip falls None)

**Result-Item:** identisch, außer `type: result`, `description: FEA Worm Gear Unit (result)`,
`simulationTool: [{toolName: "Matlab", toolVersion: null, toolSource: null}]`.
Relation (nur bei is_new): external, connection_type=hasSimulationReport,
external_system="Windchill (PDMLink) / Creo", external_id=<CAE-Nummer>,
external_link=calculation_report_download_link (skip falls None)

**Internal Relation (nur bei is_new):** connection_type=generatesResult,
source_sdm_number/revision = Model-Item, target_sdm_number/revision = Result-Item.
**Nachtrag (2026-09-03):** ursprünglich `hasModel` (Source=Result, Target=Model) geplant,
nach Diskussion auf `generatesResult` (Source=Model, Target=Result) geändert - liest sich
natürlicher ("Model generatesResult") und passt besser zur Kausalrichtung
Model -> Result.

## Implementierungsschritte (Milestones)

Jeder Meilenstein ist einzeln lauffähig und wird für sich getestet, bevor der nächste beginnt.

### M1 – Grundgerüst & Pfad-Ableitung (keine Datei-/API-Operationen)
Status: [x] erledigt
- argparse: `--input` (default Pfad zu check_data_with_reports_and_links.json), `--instance`
  (choices QA/PROD, default QA), `--limit` (int, optional), `--dummy-data` (store_true),
  `--temp-dir` (default `C:\temp\simulab`), `--registry` (default `bulk_upload_registry.json`).
- Steuerdatei laden (`json.load`).
- Funktion `derive_cae_folder(variant_path)` – parst UNC-Pfad, findet Segment vor `\model\`,
  liefert `(cae_folder_name, network_model_dir, network_result_dir)` via
  `pathlib.Path(...).parts` (Index von `"model"` suchen, davor/danach slicen).
- Hauptschleife (bis `--limit`) druckt nur: CAE-Nummer, `cae_folder_name`,
  `network_model_dir`, `network_result_dir`, geplante lokale Zielpfade. Kein Dateisystem-,
  kein API-Zugriff.
- **Test:** `python bulk_upload.py --limit 3` ausführen, Konsolenausgabe gegen 2-3 bekannte
  Einträge aus `check_data_with_reports_and_links.json` manuell prüfen (z.B. `CAE018147` →
  Ordner `CAE018147_RunIn_Geometry_Symmetry`).

### M2 – Lokale Dateivorbereitung (weiterhin ohne API)
Status: [x] erledigt
- `prepare_local_dir(local_dir, network_dir, dummy)` – löscht `local_dir` falls vorhanden
  (sauberer Re-Run), erzeugt neu; bei `dummy=True` schreibt 2 Platzhalter-.txt-Dateien; sonst
  `shutil.copytree(network_dir, local_dir)` (bei fehlendem Quellordner: Warnung drucken,
  Rückgabe `False` → Aufrufer überspringt diese CAE-Nummer).
- **NUR für Model-Item zusätzlich**: `write_variant_json_files(local_model_dir, variants)` –
  iteriert über `entry["variants"]` und schreibt für jede Variante mit
  `json_content is not None` den Inhalt als `<name>.json` nach `local_model_dir` (via
  `json.dump(..., indent=2, ensure_ascii=False)`). Läuft **immer** (unabhängig von
  `--dummy-data`), da `json_content` direkt aus der Steuerdatei stammt. Variante überspringen
  falls `json_content is None` (kommt vor, z.B. `"OLD_MCV_Loop1"` in CAE019468). `name`-Feld
  kann Backslashes enthalten (Unterordner, z.B.
  `"MCV_WheelLoop2_WormLoop1s_Zytel02\\Medina"`) → als Pfad interpretieren
  (`Path(local_model_dir, *name.split("\\"))`, parent-Verzeichnisse mit `mkdir(parents=True)`
  anlegen) statt Backslash im Dateinamen zu belassen.
- Hauptschleife ruft beide Funktionen auf, Upload wird nur als
  `print("would upload ...")` simuliert (noch kein echter API-Call).
- **Test:** `--limit 2 --dummy-data` ausführen, danach
  `C:\temp\simulab\<CAE-Ordner>\model` und `\result` im Explorer/Terminal prüfen
  (Platzhalterdateien + `<variant>.json`-Dateien vorhanden, ggf. in Unterordnern bei Namen
  mit `\`).

### M3 – Metadata-Aufbau & Registry-Helper (weiterhin ohne echten Upload)
Status: [x] erledigt
- `next_delete_index(registry)` durchsucht alle bereits in der Registry gespeicherten Namen
  (model+result, über alle CAE-Nummern) nach dem Muster `pls_delete_(\d+)_` und liefert den
  höchsten gefundenen Wert +1 (oder `1`, falls keiner gefunden wird).
- `build_item_name(folder_name, instance, index)` liefert auf QA
  `pls_delete_<index:03d>_<folder_name>`, auf PROD unverändert `folder_name`.
- `build_metadata(item_type, cae_number, folder_name, instance)` liefert das Dict wie im
  Abschnitt "Metadata-Vorlagen" (mit korrektem `simulationTool` je nach model/result), wobei
  `folder_name` bereits der fertige (ggf. präfixierte) Name ist. Ist `instance == "QA"`, wird
  `tags` um `"delete in future"` ergänzt (auf PROD bleibt `tags: []`). Für Update-Aufrufe: Kopie
  ohne `groupId`/`type`, mit zusätzlichem `changeDescription` (`build_update_metadata`).
- Registry-Einträge (`registry[cae_number]["model"|"result"]`) speichern zusätzlich zu
  `sdm_number`/`sdm_revision` auch `name`. Bei Erstanlage (`is_new`) wird pro Item (model,
  dann result) je ein neuer Index via `next_delete_index` gezogen (Zähler steigt also auch
  innerhalb eines CAE-Eintrags von model zu result); bei Updates wird der gespeicherte Name aus
  der Registry wiederverwendet statt neu berechnet.
- `build_upload_payload(directory, metadata, existing=None)` verpackt das Metadata-Dict
  zusammen mit `directory` (und bei Updates `existing_sdm_number`/`existing_sdm_revision` aus
  der Registry) zu einem kompletten `upload_directory`-Parameter-Dict (Schema wie
  `templates/upload_directory_template.json`). `write_json_file(target_dir, filename, data)`
  schreibt dieses Dict als `model_upload_directory.json`/`result_upload_directory.json` neben
  die model/result-Ordner.
- `load_registry(path)` / `save_registry(path, data)` – einfaches
  `json.load`/`json.dump(..., indent=2, ensure_ascii=False)`.
- Hauptschleife druckt das fertige Upload-Payload-Dict für model+result und schreibt es
  zusätzlich als Datei (noch kein echter API-Call aus dem Skript heraus).
- **Test:** Konsolenausgabe/Dateien gegen die Vorgaben aus "Metadata-Vorlagen" prüfen
  (Feldnamen, `simulationDomain` als Liste, `simulationTool: null` beim Model-Item,
  `tags` enthält bei `--instance QA` den Eintrag `"delete in future"`, bei PROD nicht,
  keine `groupId`/`type` im simulierten Update-Fall). **Zusätzlich:** `name` enthält bei QA
  den Präfix `pls_delete_001_...` beim ersten Lauf mit leerer Registry; bei einem zweiten Lauf
  mit bereits einem `pls_delete_003_...`-Eintrag in der Registry wird für den nächsten neuen
  Namen `pls_delete_004_...` vergeben; bei Update eines bereits bekannten CAE-Eintrags bleibt
  der ursprüngliche Name (samt Index) unverändert. **Bereits vorher verifiziert:** die
  generierte `model_upload_directory.json` wurde per echtem `simulabcli --instance QA -f
  ... upload_directory`-Aufruf getestet und hat erfolgreich ein Item angelegt (`SDM0016629`) –
  bestätigt, dass Dateiformat/Schema korrekt sind (Test war noch ohne Namenspräfix).

### M4 – Relation-Payload-Aufbau (nur Dateien, kein API-Call)
Status: [x] erledigt
- Neue Helper `build_external_relation_payload(connection_type, source, external_system,
  external_id, external_link)` und `build_internal_relation_payload(source, target)` liefern
  Dicts im Schema von `templates/create_external_relation_template.json` bzw.
  `templates/create_internal_relation_template.json` (`connection_type`, `source_sdm_number`,
  `source_sdm_revision`, ggf. `external_system`/`external_id`/`external_version`/`external_link`
  bzw. `target_sdm_number`/`target_sdm_revision`, `internal`, `access_token`).
- Da zu diesem Zeitpunkt noch kein echter Upload stattgefunden hat (M5 kommt erst danach),
  existieren die echten `sdm_number`/`sdm_revision` von Model/Result noch nicht → alle
  `source_sdm_number`/`source_sdm_revision`/`target_sdm_number`/`target_sdm_revision`-Felder
  werden vorerst als Platzhalter `null` geschrieben. Diese werden in der Ausführungs-Milestone
  (M7) durch die echten Werte aus dem Upload-Ergebnis/der Registry ersetzt, bevor der
  eigentliche `create_relation`-Call erfolgt.
- Nur schreiben wenn `is_new` (CAE-Nummer noch nicht in Registry). Externe Relation-Datei für
  Model nur schreiben, wenn `caedb_url` vorhanden ist; für Result nur wenn
  `calculation_report_download_link` vorhanden ist (sonst Skip + Warnung, kein Platzhalter-Call).
  Interne Relation-Datei immer wenn `is_new` (kein Link-Bezug nötig).
- Dateien (alle in `local_cae_dir`, also neben `model_upload_directory.json`/
  `result_upload_directory.json`):
  - `relation_external_model.json` (connection_type=isBasedOnSimulationOrder,
    external_system=CAE-DB, external_id=<CAE-Nummer>, external_link=caedb_url)
  - `relation_external_result.json` (connection_type=hasSimulationReport,
    external_system="Windchill (PDMLink) / Creo", external_id=<CAE-Nummer>,
    external_link=calculation_report_download_link)
  - `relation_internal_model_result.json` (connection_type=generatesResult, internal=true,
    source=Model-Item, target=Result-Item)
- Hauptschleife druckt die 3 (oder weniger, falls Links fehlen) Payload-Dicts und schreibt sie
  zusätzlich als Datei.
- **Test:** `--limit 2 --dummy-data` ausführen (leere Registry → beide Einträge `is_new`),
  prüfen dass für beide CAE-Nummern die relation_*.json Dateien neben
  `model_upload_directory.json` liegen; Felder gegen Templates prüfen (`connection_type`,
  `external_system`, `external_id`, `external_link` korrekt gemappt, `null`-Platzhalter für
  alle sdm-Felder). **Test 2:** CAE-Nummer mit fehlendem `calculation_report_download_link`
  (z.B. `CAE019016`) verwenden → `relation_external_result.json` wird NICHT erzeugt, Warnung
  in Konsole, die anderen beiden Relation-Dateien trotzdem.

### M5 – Echter Upload, Create-Pfad (QA)
Status: [x] erledigt
- `create_or_update_item(payload)` importiert `simulabcli` und ruft `simulabcli.cli.
  upload_directory(**payload)` mit dem in M3 bereits gebauten `model_payload`/`result_payload`
  wirklich auf (zunächst nur Create-Zweig, da Registry zu Beginn leer ist). Gibt `result` dict
  zurück (`sdm_number`, `sdm_revision`). Registry wird nach jedem Call sofort gespeichert
  (crash-sicher).
- **Test:** `--limit 1 --dummy-data --instance QA` ausführen. Erwartet: zwei neue SDM-Items
  (sdm_number in Konsole + in `bulk_upload_registry.json`), beide mit Tag `"delete in future"`.
  Optional Stichprobe über `get_metadata` in QA (Tag prüfen).

### M6 – Update-Pfad
Status: [x] erledigt
- **Korrektur nach User-Feedback:** Auf QA sollen Testdaten bei JEDEM Lauf als NEUES Item
  angelegt werden (fortlaufender `pls_delete_<idx>_`-Name), auch wenn die CAE-Nummer schon in
  der Registry steht – die Registry ist auf QA nur noch Namens-/Index-Gedächtnis, nicht
  Idempotenz-Kriterium. NUR auf PROD verhindert ein Registry-Treffer eine Neuanlage und löst
  stattdessen den Update-Pfad aus (`existing_sdm_number`/`existing_sdm_revision` gesetzt,
  `changeDescription` statt `groupId`/`type`). Umgesetzt über
  `is_new = args.instance == "QA" or cae_number not in registry`.
- **Test durchgeführt:** `--limit 1 --dummy-data --instance QA` (CAE018147, bereits mit
  `pls_delete_001_`/`002_` in Registry) zweimal ausgeführt. Ergebnis: statt Update wurden
  erwartungsgemäß neue Items `pls_delete_003_...`/`pls_delete_004_...` (SDM0016636/SDM0016637)
  angelegt, Registry-Eintrag für CAE018147 wurde auf die neuesten sdm_number/name überschrieben,
  Relation-Payload-Dateien wurden (da `is_new` jetzt wieder True) erneut geschrieben.
  PROD-Update-Pfad (Registry-basiert, keine Neuanlage) bleibt unverändert wie zuvor getestet.
- **Nachtrag (Registry-Kollision QA/PROD):** die Registry war ursprünglich nur nach CAE-Nummer
  geschlüsselt (`registry[cae_number]["model"/"result"]`) – ein späterer PROD-Lauf hätte damit
  fälschlich den QA-Eintrag als "existing" gelesen und versucht, das QA-Item über die
  PROD-Instanz zu updaten. Fix: Registry ist jetzt zusätzlich nach Instanz verschachtelt
  (`registry[cae_number][instance]["model"/"result"]`), `next_delete_index` durchsucht alle
  Instanzen. `bulk_upload_registry.json` wurde auf das neue Schema migriert (bestehende
  Einträge unter `"QA"` verschachtelt). Erneut mit `--limit 1 --dummy-data --instance QA`
  getestet: neue Items `pls_delete_005_...`/`pls_delete_006_...` (SDM0016638/SDM0016639)
  korrekt unter `registry["CAE018147"]["QA"]` abgelegt.

### M7 – Relations: Ausführung
Status: [x] erledigt
- `execute_relation(local_cae_dir, filename, source=None, target=None)` lädt die in M4
  geschriebene `relation_*.json` (falls vorhanden), ersetzt `source_sdm_number`/
  `source_sdm_revision` (bzw. zusätzlich `target_sdm_number`/`target_sdm_revision`) durch die
  echten Werte aus dem Upload-Ergebnis (`model_result`/`result_result`, bereits in M5 vorhanden)
  und ruft `simulabcli.cli.create_relation(**payload)` auf. Fehlt die Datei (Link war in M4
  nicht vorhanden), wird sauber übersprungen (Warnung, kein Fehler).
- **Test 1:** neue, noch nicht verarbeitete CAE-Nummer mit `--limit 1 --dummy-data
  --instance QA` laufen lassen, prüfen dass alle vorhandenen Relation-Calls ohne Fehler
  durchlaufen.
- **Test 2:** CAE-Nummer mit fehlendem `calculation_report_download_link` (z.B.
  `CAE019016`) verwenden, prüfen dass die betroffene externe Relation sauber übersprungen
  wird (kein Fehler, Warnung in Konsole, da Datei aus M4 schon fehlt).

### M8 – Batch-Lauf, Summary & Idempotenz
Status: [x] erledigt
- Abschluss-Summary: Anzahl neu/aktualisiert/übersprungen, per `print()` am Ende des Laufs.
- **Test:** größerer `--limit` (z.B. 5-10) mit `--dummy-data --instance QA` laufen lassen,
  danach denselben Befehl ein zweites Mal ausführen → alle Einträge müssen beim zweiten Lauf
  über den Update-Pfad laufen, Summary-Zahlen prüfen (0 neu, alle aktualisiert).

### M9 – Gezielter Upload per --cae-numbers
Status: [x] erledigt
- Neuer CLI-Flag `--cae-numbers` (`nargs="+"`, Default `None`) in `parse_args()`: erlaubt es,
  gezielt eine oder mehrere CAE-Nummern zu verarbeiten statt den kompletten Datensatz aus
  `--input`. Funktioniert unverändert in QA und PROD (reine Vorfilterung, Create/Update-Logik
  bleibt unangetastet).
- Vor der Hauptschleife: ist `--cae-numbers` gesetzt, wird eine Liste `entries` gebaut, indem
  für jede angegebene CAE-Nummer geprüft wird ob sie als Key in `data` existiert (Reihenfolge =
  CLI-Reihenfolge); fehlt eine, wird eine Warnung gedruckt und sie wird übersprungen (kein
  Abbruch). Ist der Flag nicht gesetzt, bleibt `entries = list(data.items())` wie bisher.
- Schleifenkopf `for cae_number, entry in data.items():` wird zu
  `for cae_number, entry in entries:`. Die bestehende `--limit`-Abbruchbedingung wird
  zusätzlich an `args.cae_numbers is None` geknüpft, d.h. `--cae-numbers` ignoriert `--limit`
  vollständig (bewusst keine Fehlermeldung bei gleichzeitiger Nutzung).
- Keine Änderung an Registry-Schema, `is_new`-Logik oder Metadata-Aufbau – QA legt weiterhin
  bei jedem Lauf neu an (`pls_delete_<idx>_`), PROD nutzt weiter registry-basiertes Update.
- **Test 1:** `--cae-numbers CAE018147 --dummy-data --instance QA` → nur dieser eine Eintrag
  wird verarbeitet, neues Item mit nächstem `pls_delete_<idx>_`-Index.
- **Test 2:** `--cae-numbers CAE018147 CAE019016 --dummy-data --instance QA` → beide Einträge
  verarbeitet, Summary zeigt 2 neu.
- **Test 3:** `--cae-numbers CAE_NICHT_VORHANDEN --dummy-data --instance QA` → Warnung, kein
  Crash, Summary 0/0/0.
- **Test 4:** `--cae-numbers CAE018147 --limit 1 --dummy-data --instance QA` → `--limit` bleibt
  wirkungslos (nur zur Doku, kein Fehlerfall).
- PROD wird nicht per echtem Testlauf verifiziert (reale API-Auswirkung) – stattdessen
  Code-Review, dass die Filterung instanzunabhängig VOR der bestehenden
  `is_new = args.instance == "QA" or not already_registered`-Logik greift.
- **Test durchgeführt:** `--cae-numbers CAE018147 --dummy-data --instance QA` → nur dieser
  Eintrag verarbeitet, neues Item `pls_delete_037_.../pls_delete_038_...`
  (SDM0016671/SDM0016672) angelegt. `--cae-numbers CAE_NICHT_VORHANDEN --dummy-data
  --instance QA` → Warnung ausgegeben, Summary 0/0/0, kein Crash.

## Relevante Dateien
- `bulk_upload.py` (NEU, Projekt-Root) – Hauptskript, alles darin (Helper-Funktionen +
  `if __name__ == "__main__":`-Block), analog zum Stil von
  [use-case_fea-worm-gear/scripts/data_collector.py](use-case_fea-worm-gear/scripts/data_collector.py).
- `bulk_upload_registry.json` (NEU, wird zur Laufzeit angelegt, Projekt-Root).
- `use-case_fea-worm-gear/scripts/check_data_with_reports_and_links.json` – Steuerdatei
  (Default-Input).
- `.venv/Lib/site-packages/simulabcli/cli.py` – `upload_directory`, `create_relation` (Referenz
  für Funktionssignaturen).
- `.venv/Lib/site-packages/simulabcli/_item_schema.py` – Pydantic-Schema (Pflichtfelder,
  `extra="forbid"`, Update-Modell ohne groupId/type).
- `templates/upload_directory_template.json`, `templates/upload_existing_directory_template.json`,
  `templates/create_external_relation_template.json`,
  `templates/create_internal_relation_template.json` – Referenz für Dict-Struktur.

## Verification
Tests sind je Meilenstein oben (M1-M8) definiert. Nach M8 zusätzlich optional:
`--limit 2 --instance QA` ohne `--dummy-data` (falls Netzlaufwerk erreichbar) → echte Kopie
von `model`/`result`-Ordner nach `C:\temp\simulab` prüfen.

**Bekannter Altlast-Eintrag:** Beim manuellen Verifizieren der M3-Payload-Datei (vor M4) wurde
per direktem `simulabcli`-CLI-Aufruf bereits real ein QA-Item angelegt: `SDM0016629`
(CAE018147, type model, Tag `"delete in future"` gesetzt). Ist noch nicht in
`bulk_upload_registry.json` erfasst (Registry existiert zu dem Zeitpunkt noch nicht) – bei
Bedarf manuell nachtragen oder als bekannten Test-Datensatz auf QA ignorieren.

## Scope-Ausschlüsse
- Kein Löschen/Zurücksetzen von Items (keine Delete-API vorhanden) – Ersatz ist die
  `"delete in future"`-Tag-Konvention auf QA.
- Keine Vorab-Validierung der Metadata-Werte gegen die API (Skript lässt API-Fehler einfach
  durchschlagen, kein try/except-Wrapping um jeden Call).
- Kein `--metadata-only`/`--dry-run`-Schalter ohne API-Calls (aus altem Plan verworfen) –
  stattdessen `--dummy-data` (echte API-Calls mit Platzhalterdateien) und `--limit`
  (Mengensteuerung) wie vom User gefordert.
- Kein Multithreading/Parallelisierung (bewusst einfach, sequenziell pro CAE-Nummer).
