# Plan: search_linked_tasks.py — rekursive Task-Suche

Neues Skript `use-case_sil-modell_vssp/scripts/search_linked_tasks.py`, das ausgehend
von einer task_id per BFS rekursiv sowohl `sub_tasks` als auch `linked_tasks` verfolgt
und alle gefundenen Tasks (dedupliziert, zyklensicher) als JSON-Liste ausgibt.
Basis: bestehende Fetch-Funktionen aus `task_fetcher.py` (Wiederverwendung per Import).

## Steps

1. In `search_linked_tasks.py`: aus `task_fetcher` importieren:
   `fetch_task_breadcrumb`, `fetch_sub_tasks`, `fetch_linked_tasks`.
2. Traversal-Funktion `search_linked_tasks(root_task_id)`:
   - BFS mit `collections.deque`, Startknoten `(root_task_id, parent_id=None, relation_type="root", depth=0)`.
   - `visited: set[int]` verhindert Zyklen/Duplikate — Task wird nur beim ersten Auftreten aufgenommen und expandiert.
   - Für Root: einmalig `fetch_task_breadcrumb` aufrufen für `task_number`/`thema` (da kein Parent diese Info liefert).
   - Für jeden Knoten: `fetch_sub_tasks(task_id)` → Kinder mit `relation_type="sub_task"`, Felder `aufgabeId`/`taskNumber`/`thema`.
   - `fetch_linked_tasks(task_id)` → Kinder mit `relation_type=<linkType>` (z.B. "depends on"), Felder `taskId`/`taskNumber`/`taskName`/`status`.
   - Metadaten für Kinder werden direkt aus der Parent-Response übernommen (keine zusätzliche breadcrumb-Abfrage pro Kind — spart API-Calls).
   - Jeder Knoten wird als Dict gesammelt: `{task_id, task_number, thema, relation_type, parent_task_id, depth, status}`.
   - Fehlerbehandlung: `try/except requests.exceptions.RequestException` je Fetch-Call — bei Fehler Warnung loggen (print), Knoten bleibt in Ergebnis (ggf. ohne Kinder), Traversal läuft weiter.
3. Ausgabe-Struktur (JSON):
   ```json
   {
     "root_task_id": 524049,
     "root_task_number": "CAE025316",
     "root_thema": "...",
     "task_count": 4,
     "tasks": [ ... ]
   }
   ```
   Datei: `{root_task_number oder root_task_id}_linked_tasks.json` (analog zu bestehendem `{cae_number}_task_summary.json` Namensschema).
4. CLI: `argparse` mit Pflicht-Argument `task_id` (int); `if __name__ == "__main__":` liest `sys.argv` via argparse, ruft Traversal auf, schreibt Datei, druckt Kurzsummary (Anzahl gefundener Tasks).

## Relevante Dateien

- [use-case_sil-modell_vssp/scripts/task_fetcher.py](use-case_sil-modell_vssp/scripts/task_fetcher.py) — Basis, Funktionen `fetch_task_breadcrumb`, `fetch_sub_tasks`, `fetch_linked_tasks`, `fetch_response` werden importiert/wiederverwendet, nicht dupliziert.
- `use-case_sil-modell_vssp/scripts/search_linked_tasks.py` (neu) — Traversal + CLI.

## Verifikation

1. Manueller Lauf: `python search_linked_tasks.py 524049` (bekannte Beispiel-ID aus `CAE025316_task_summary.json`) — prüfen, dass `sub_tasks` (524456, 524455) und `linked_tasks` (524042) in der Ausgabe auftauchen.
2. Prüfen, dass bei zyklischen/mehrfach verlinkten Tasks keine Duplikate/Endlosschleife entstehen (visited-Set greift).
3. JSON-Output-Datei auf Struktur/Vollständigkeit prüfen (`task_count` == `len(tasks)`).

## Entscheidungen (aus Rückfragen)

- Rekursions-Scope: sowohl `sub_tasks` als auch `linked_tasks` werden verfolgt.
- Keine Tiefenbegrenzung, stattdessen Zyklenerkennung via visited-Set.
- Keine zusätzlichen `technical_reports` pro Task (nur Metadaten: id, taskNumber, thema, relation_type, parent, depth).
- Ausgabe als JSON-Datei (analog `task_summary.json`).
- `task_id` wird als CLI-Argument übergeben (nicht hardcodiert).
