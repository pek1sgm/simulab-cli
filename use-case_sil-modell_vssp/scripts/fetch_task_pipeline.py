import argparse
import json

from search_linked_tasks import search_linked_tasks
from task_fetcher import fetch_task_summary


def run_pipeline(root_task_id):
    """Führt search_linked_tasks und anschließend task_fetcher für alle gefundenen Tasks aus."""
    linked_tasks_result = search_linked_tasks(root_task_id)
    output_name = linked_tasks_result.get("root_task_number") or linked_tasks_result["root_task_id"]

    linked_tasks_path = f"{output_name}_linked_tasks.json"
    with open(linked_tasks_path, "w", encoding="utf-8") as f:
        json.dump(linked_tasks_result, f, indent=2, ensure_ascii=False)
    print(f"{linked_tasks_result['task_count']} Tasks gefunden, geschrieben nach {linked_tasks_path}")

    task_summaries = []
    for task in linked_tasks_result["tasks"]:
        task_id = task.get("task_id")
        try:
            task_summaries.append(fetch_task_summary(task_id))
        except Exception as exc:
            print(f"Warnung: task_summary für {task_id} fehlgeschlagen: {exc}")

    task_summaries_path = f"{output_name}_task_summaries.json"
    with open(task_summaries_path, "w", encoding="utf-8") as f:
        json.dump(task_summaries, f, indent=2, ensure_ascii=False)
    print(f"{len(task_summaries)} Task-Summaries geschrieben nach {task_summaries_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sucht rekursiv verlinkte/untergeordnete Tasks ab einer Aufgaben-ID und holt anschließend die Task-Summaries.")
    parser.add_argument("task_id", type=int, help="Start-Aufgaben-ID (caedb)")
    args = parser.parse_args()
    run_pipeline(args.task_id)
