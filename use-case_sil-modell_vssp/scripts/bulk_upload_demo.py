"""Create the CAE025316 demo items and external relations in simuLAB QA.

The script creates metadata-only model items. Files and internal relations are
intentionally left for manual follow-up. Without --apply it only prints a plan.
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

import simulabcli.cli
from simulabcli._instance import set_instance


logging.getLogger("simulabcli._requests").setLevel(logging.CRITICAL)

USE_CASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    USE_CASE_DIR / "data" / "ref_CAE025316" / "CAE025316_task_summaries.json"
)
DEFAULT_REGISTRY = (
    USE_CASE_DIR / "data" / "CAE025316_bulk_upload_registry.json"
)
DEFAULT_CAE_NUMBERS = (
    "CAE025316",
    "CAE025309",
    "CAE025310",
    "CAE024292",
    "CAE023231",
    "CAE024489",
)

CAE_CONNECTION_TYPE = "isBasedOnSimulationOrder"
CAE_EXTERNAL_SYSTEM = "CAE-DB"
REPORT_CONNECTION_TYPE = "hasSimulationReport"
REPORT_EXTERNAL_SYSTEM = "Windchill (PDMLink) / Creo"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument(
        "--cae-numbers",
        nargs="+",
        default=list(DEFAULT_CAE_NUMBERS),
        metavar="CAE_NUMBER",
    )
    parser.add_argument("--group-id", default="vm-simulation")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create items and relations in QA. Default: dry-run only.",
    )
    return parser.parse_args()


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_registry(path):
    if not path.exists():
        return {"items": {}, "relations": {}}
    registry = load_json(path)
    registry.setdefault("items", {})
    registry.setdefault("relations", {})
    return registry


def save_registry(path, registry):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(registry, file, indent=2, ensure_ascii=False)
        file.write("\n")
    temporary_path.replace(path)


def select_tasks(task_summaries, cae_numbers):
    tasks_by_cae = {task["cae_number"]: task for task in task_summaries}
    missing = [
        cae_number for cae_number in cae_numbers if cae_number not in tasks_by_cae
    ]
    if missing:
        raise ValueError(f"CAE tasks not found: {', '.join(missing)}")

    selected = [tasks_by_cae[cae_number] for cae_number in cae_numbers]
    without_reports = [
        task["cae_number"]
        for task in selected
        if not task.get("technical_reports")
    ]
    if without_reports:
        raise ValueError(
            "Selected tasks have no technical reports: "
            + ", ".join(without_reports)
        )
    return selected


def compact_name(value, max_length=150):
    compacted = re.sub(r"\s+", " ", value).strip()
    return compacted[:max_length].rstrip()


def build_metadata(task, group_id):
    cae_number = task["cae_number"]
    task_name = compact_name(task["task_name"])
    return {
        "groupId": group_id,
        "name": compact_name(f"pls_delete_demo_{cae_number}_{task_name}", 200),
        "type": "model",
        "status": "In Work",
        "description": (
            f"simuLAB QA demo for CAE-DB task {cae_number} "
            f"(task ID {task['task_id']}): {task_name}"
        ),
        "projectNumber": cae_number,
        "tags": ["delete in future", "qa-demo", "sil-vssp"],
    }


def build_relation_payload(
    connection_type, source, external_system, external_id, external_link
):
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


def build_relation_actions(task):
    cae_number = task["cae_number"]
    actions = [
        {
            "key": f"caedb:{cae_number}",
            "connection_type": CAE_CONNECTION_TYPE,
            "external_system": CAE_EXTERNAL_SYSTEM,
            "external_id": cae_number,
            "external_link": task["task_url"],
        }
    ]
    for report in task["technical_reports"]:
        report_id = report["report"]
        actions.append(
            {
                "key": f"windchill:{cae_number}:{report_id}",
                "connection_type": REPORT_CONNECTION_TYPE,
                "external_system": REPORT_EXTERNAL_SYSTEM,
                "external_id": report_id,
                "external_link": report["download_link"],
            }
        )
    return actions


def build_plan(tasks, group_id):
    return [
        {
            "cae_number": task["cae_number"],
            "task_id": task["task_id"],
            "metadata": build_metadata(task, group_id),
            "relations": build_relation_actions(task),
        }
        for task in tasks
    ]


def print_plan(plan, apply):
    relation_count = sum(len(item["relations"]) for item in plan)
    mode = "APPLY to QA" if apply else "DRY-RUN"
    print(f"=== {mode}: CAE025316 simuLAB demo ===")
    for item in plan:
        report_ids = [
            relation["external_id"]
            for relation in item["relations"]
            if relation["external_system"] == REPORT_EXTERNAL_SYSTEM
        ]
        print(
            f"{item['cae_number']} (task {item['task_id']}): "
            f"model item, reports={', '.join(report_ids)}"
        )
    print(f"Items: {len(plan)}")
    print(f"External relations: {relation_count} (CAE-DB + Windchill)")
    print("Files: 0; internal relations: 0")


def create_item(metadata):
    return simulabcli.cli.upload_list([], metadata, access_token=None)


def apply_plan(plan, registry, registry_path):
    stats = {
        "items_created": 0,
        "items_reused": 0,
        "relations_created": 0,
        "relations_reused": 0,
        "failed": 0,
    }

    for planned_item in plan:
        cae_number = planned_item["cae_number"]
        item = registry["items"].get(cae_number)
        if item:
            stats["items_reused"] += 1
            print(
                f"[REUSE] {cae_number}: "
                f"{item['sdm_number']}-{item['sdm_revision']}"
            )
        else:
            try:
                response = create_item(planned_item["metadata"])
                item = {
                    "name": planned_item["metadata"]["name"],
                    "sdm_number": response["sdm_number"],
                    "sdm_revision": response["sdm_revision"],
                }
                registry["items"][cae_number] = item
                save_registry(registry_path, registry)
                stats["items_created"] += 1
                print(
                    f"[CREATED] {cae_number}: "
                    f"{item['sdm_number']}-{item['sdm_revision']}"
                )
            except Exception as error:
                stats["failed"] += 1
                print(
                    f"[ERROR] {cae_number}: item creation failed: {error}",
                    file=sys.stderr,
                )
                continue

        for relation in planned_item["relations"]:
            relation_key = relation["key"]
            if relation_key in registry["relations"]:
                stats["relations_reused"] += 1
                print(f"  [REUSE] {relation_key}")
                continue
            try:
                payload = build_relation_payload(
                    relation["connection_type"],
                    item,
                    relation["external_system"],
                    relation["external_id"],
                    relation["external_link"],
                )
                simulabcli.cli.create_relation(**payload)
                registry["relations"][relation_key] = {
                    "source_sdm_number": item["sdm_number"],
                    "connection_type": relation["connection_type"],
                    "external_id": relation["external_id"],
                }
                save_registry(registry_path, registry)
                stats["relations_created"] += 1
                print(f"  [CREATED] {relation_key}")
            except Exception as error:
                stats["failed"] += 1
                print(f"  [ERROR] {relation_key}: {error}", file=sys.stderr)

    return stats


def main():
    args = parse_args()
    tasks = select_tasks(load_json(args.input), args.cae_numbers)
    plan = build_plan(tasks, args.group_id)
    print_plan(plan, args.apply)

    if not args.apply:
        print("No changes made. Use --apply to write to simuLAB QA.")
        return 0

    set_instance("QA")
    registry = load_registry(args.registry)
    stats = apply_plan(plan, registry, args.registry)
    print("\n=== Summary ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
