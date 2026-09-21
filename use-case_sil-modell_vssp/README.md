# SiL-Modell VSSP QA-Demo

`scripts/bulk_upload_demo.py` legt sechs reporttragende CAE-Tasks als
Metadaten-only Model-Items in simuLAB QA an. Automatisch erstellt werden nur
externe Relationen zur CAE-DB und zu den in der Steuerdatei genannten
Windchill-Reports.

Dry-run ohne API-Schreibzugriff:

```powershell
uv run python use-case_sil-modell_vssp/scripts/bulk_upload_demo.py
```

Anlage in QA:

```powershell
uv run python use-case_sil-modell_vssp/scripts/bulk_upload_demo.py --apply
```

Optional kann die Auswahl begrenzt werden:

```powershell
uv run python use-case_sil-modell_vssp/scripts/bulk_upload_demo.py `
  --cae-numbers CAE025316 --apply
```

Die Registry wird unter `data/CAE025316_bulk_upload_registry.json` angelegt.
Sie verhindert bei Wiederholungen doppelte Items und Relationen. Wird die
Registry entfernt oder manuell veraendert, kann das zu Duplikaten in QA
fuehren.

Dateien, UNC-Daten, interne Relationen und weitere fachliche Verknuepfungen
werden nicht durch das Skript verarbeitet und muessen manuell ergaenzt werden.