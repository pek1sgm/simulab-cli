import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "use-case_sil-modell_vssp"
    / "scripts"
    / "bulk_upload_demo.py"
)
SPEC = importlib.util.spec_from_file_location("bulk_upload_demo", SCRIPT_PATH)
bulk_upload_demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bulk_upload_demo)


class BulkUploadDemoTests(unittest.TestCase):
    def build_default_plan(self):
        summaries = bulk_upload_demo.load_json(bulk_upload_demo.DEFAULT_INPUT)
        tasks = bulk_upload_demo.select_tasks(
            summaries, bulk_upload_demo.DEFAULT_CAE_NUMBERS
        )
        return bulk_upload_demo.build_plan(tasks, "vm-simulation")

    def test_default_plan_has_only_report_tasks_and_external_relations(self):
        plan = self.build_default_plan()

        self.assertEqual(6, len(plan))
        self.assertEqual(12, sum(len(item["relations"]) for item in plan))
        for item in plan:
            systems = [
                relation["external_system"] for relation in item["relations"]
            ]
            self.assertEqual(
                [
                    bulk_upload_demo.CAE_EXTERNAL_SYSTEM,
                    bulk_upload_demo.REPORT_EXTERNAL_SYSTEM,
                ],
                systems,
            )
            self.assertEqual("model", item["metadata"]["type"])

    def test_select_tasks_rejects_task_without_report(self):
        summaries = bulk_upload_demo.load_json(bulk_upload_demo.DEFAULT_INPUT)

        with self.assertRaisesRegex(ValueError, "CAE025726"):
            bulk_upload_demo.select_tasks(summaries, ["CAE025726"])

    def test_create_item_uses_empty_file_list(self):
        metadata = self.build_default_plan()[0]["metadata"]
        response = {"sdm_number": "SDM0000001", "sdm_revision": "001"}

        with patch.object(
            bulk_upload_demo.simulabcli.cli,
            "upload_list",
            return_value=response,
        ) as upload_list:
            self.assertEqual(response, bulk_upload_demo.create_item(metadata))

        upload_list.assert_called_once_with([], metadata, access_token=None)

    def test_apply_plan_reuses_registry_without_api_calls(self):
        plan = self.build_default_plan()[:1]
        cae_number = plan[0]["cae_number"]
        relation_entries = {
            relation["key"]: {"external_id": relation["external_id"]}
            for relation in plan[0]["relations"]
        }
        registry = {
            "items": {
                cae_number: {
                    "name": "existing",
                    "sdm_number": "SDM0000001",
                    "sdm_revision": "001",
                }
            },
            "relations": relation_entries,
        }

        with tempfile.TemporaryDirectory() as directory, patch.object(
            bulk_upload_demo, "create_item"
        ) as create_item, patch.object(
            bulk_upload_demo.simulabcli.cli, "create_relation"
        ) as create_relation:
            stats = bulk_upload_demo.apply_plan(
                plan, registry, Path(directory) / "registry.json"
            )

        create_item.assert_not_called()
        create_relation.assert_not_called()
        self.assertEqual(1, stats["items_reused"])
        self.assertEqual(2, stats["relations_reused"])
        self.assertEqual(0, stats["failed"])


if __name__ == "__main__":
    unittest.main()
