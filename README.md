execute: uv run [fetch_task_pipeline.py](use-case_sil-modell_vssp/scripts/fetch_task_pipeline.py) <taskid> # e.g. 524049
# führt search_linked_tasks.py und task_fetcher.py nacheinander aus, schreibt CAE025316_linked_tasks.json und CAE025316_task_summaries.json

## QA demo bulk upload

Use case: [use-case_sil-modell_vssp/scripts/bulk_upload_demo.py](use-case_sil-modell_vssp/scripts/bulk_upload_demo.py)

- Zweck: Demo-Upload in simuLAB QA mit den reporttragenden CAE-Tasks aus CAE025316.
- Scope: nur SDM-Item-Anlage plus externe Relationen.
  - CAE-DB: `isBasedOnSimulationOrder`
  - Windchill-Reports: `hasSimulationReport`
- Nicht enthalten: Datei-Uploads, UNC-Daten, interne Relationen, fachliche Nachbeziehungen.

Dry-run (ohne Schreiben):

```bash
uv run python use-case_sil-modell_vssp/scripts/bulk_upload_demo.py
```

Ausführen in QA:

```bash
uv run python use-case_sil-modell_vssp/scripts/bulk_upload_demo.py --apply
```

Hinweis: Dateien und weitere fachliche Relationen werden bewusst manuell nachgezogen. Der Demo-Skriptteil dient zur schnellen Basis für QA-Visualisierung und Ablaufdemo.