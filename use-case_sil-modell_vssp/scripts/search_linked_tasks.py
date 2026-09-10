import argparse
import json
from collections import deque

import requests

from task_fetcher import fetch_linked_tasks, fetch_sub_tasks, fetch_task_breadcrumb


def _extract_list(response_json):
    """caeResponseData ist bei Fehlern (z.B. Task not found) ein Dict statt einer Liste."""
    data = response_json.get("caeResponseData")
    return data if isinstance(data, list) else []


def search_linked_tasks(root_task_id):
    """Durchsucht BFS-artig sub_tasks und linked_tasks ab einer Root-Task-ID und liefert alle gefundenen Tasks."""
    try:
        breadcrumb = fetch_task_breadcrumb(root_task_id).get("caeResponseData", {})
    except requests.exceptions.RequestException as exc:
        print(f"Warnung: breadcrumb für {root_task_id} fehlgeschlagen: {exc}")
        breadcrumb = {}

    root_task_number = breadcrumb.get("taskNumber")
    root_thema = breadcrumb.get("thema")

    visited = {root_task_id}
    queue = deque([(root_task_id, None, "root", 0, root_task_number, root_thema, None)])
    tasks = []

    while queue:
        task_id, parent_task_id, relation_type, depth, task_number, thema, status = queue.popleft()
        tasks.append({
            "task_id": task_id,
            "task_number": task_number,
            "thema": thema,
            "relation_type": relation_type,
            "parent_task_id": parent_task_id,
            "depth": depth,
            "status": status,
        })

        try:
            sub_tasks = _extract_list(fetch_sub_tasks(task_id))
        except requests.exceptions.RequestException as exc:
            print(f"Warnung: sub_tasks für {task_id} fehlgeschlagen: {exc}")
            sub_tasks = []
        for st in sub_tasks:
            child_id = st.get("aufgabeId")
            if child_id is None or child_id in visited:
                continue
            visited.add(child_id)
            queue.append((child_id, task_id, "sub_task", depth + 1, st.get("taskNumber"), st.get("thema"), None))

        try:
            linked_tasks = _extract_list(fetch_linked_tasks(task_id))
        except requests.exceptions.RequestException as exc:
            print(f"Warnung: linked_tasks für {task_id} fehlgeschlagen: {exc}")
            linked_tasks = []
        for lt in linked_tasks:
            child_id = lt.get("taskId")
            if child_id is None or child_id in visited:
                continue
            visited.add(child_id)
            queue.append((
                child_id, task_id, lt.get("linkType", "linked"), depth + 1,
                lt.get("taskNumber"), lt.get("taskName"), lt.get("status"),
            ))

    return {
        "root_task_id": root_task_id,
        "root_task_number": root_task_number,
        "root_thema": root_thema,
        "task_count": len(tasks),
        "tasks": tasks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rekursive Suche nach allen verlinkten/untergeordneten Tasks ab einer Aufgaben-ID.")
    parser.add_argument("task_id", type=int, help="Start-Aufgaben-ID (caedb)")
    args = parser.parse_args()

    result = search_linked_tasks(args.task_id)
    output_name = result.get("root_task_number") or result["root_task_id"]
    output_path = f"{output_name}_linked_tasks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"{result['task_count']} Tasks gefunden, geschrieben nach {output_path}")
