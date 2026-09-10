import argparse
import json

import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv('WINDCHILL_BASE_URL')
API_KEY = os.getenv('WINDCHILL_API_KEY')
BASE_URL_CAE_DB = os.getenv('CAE_DB_BASE_URL')

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def fetch_response(url, timeout=10):
    """Holt die Response für die gegebene URL via Windows-SSO (NTLM/Kerberos) und gibt sie zurück."""
    response = requests.get(url, auth=HttpNegotiateAuth(), timeout=timeout)
    response.raise_for_status()
    return response


def fetch_task_breadcrumb(task_id):
    """Holt die Breadcrumb-Daten (Projekt/Gruppe/Thema) für eine caedb-Aufgaben-ID."""
    url = f"https://rb-wam.bosch.com/caedb/breadcrumb/fetch-parent/projectType/AUFGABEN/id/{task_id}"
    return fetch_response(url).json()


def fetch_sub_tasks(task_id):
    """Holt die Unter-Aufgaben für eine caedb-Aufgaben-ID."""
    url = f"https://rb-wam.bosch.com/caedb/aufgaben/uebersicht/aufgabe/{task_id}/fetch/unter-aufgaben"
    return fetch_response(url).json()


def fetch_all_documents(task_id):
    """Holt alle Dokumente für eine caedb-Aufgaben-ID."""
    url = f"https://rb-wam.bosch.com/caedb/aufgaben/uebersicht/aufgabe/{task_id}/fetch-all-dokumente/"
    return fetch_response(url).json()


def fetch_linked_tasks(task_id):
    """Holt die verlinkten Aufgaben für eine caedb-Aufgaben-ID."""
    url = f"https://rb-wam.bosch.com/caedb/aufgaben/uebersicht/aufgabe/{task_id}/fetch/linked-tasks"
    return fetch_response(url).json()


def fetch_project_tasks(teil_project_id):
    """Holt alle Aufgaben eines Teilprojekts."""
    url = f"https://rb-wam.bosch.com/caedb/projekte/uebersicht/aufgaben/{teil_project_id}"
    return fetch_response(url).json()


def fetch_report_download_link(report_number):
    """Fragt den Windchill-Downloadlink für eine Report-Nummer ab."""
    response = requests.get(
        f"{BASE_URL}/guess_document",
        headers=headers,
        params={"report_number": report_number},
        timeout=10
    )
    if response.status_code != 200:
        return None
    return response.json().get("link_direct")


def _extract_list(response_json):
    """caeResponseData ist bei Fehlern (z.B. Task not found) ein Dict statt einer Liste."""
    data = response_json.get("caeResponseData")
    return data if isinstance(data, list) else []


def fetch_task_summary(task_id):
    """Sammelt alle caedb-Informationen zu einer Aufgaben-ID in einer konsolidierten Struktur."""
    task_data = fetch_task_breadcrumb(task_id)
    task_info = task_data.get("caeResponseData", {})
    if not isinstance(task_info, dict):
        task_info = {}

    sub_tasks_list = [
        {
            "aufgabeId": st.get("aufgabeId"),
            "taskNumber": st.get("taskNumber"),
            "thema": st.get("thema"),
        }
        for st in _extract_list(fetch_sub_tasks(task_id))
    ]

    linked_tasks_list = _extract_list(fetch_linked_tasks(task_id))

    task_data = None
    teil_project_id = task_info.get("teilProjectId")
    if teil_project_id is not None:
        project_tasks = _extract_list(fetch_project_tasks(teil_project_id))
        matching_task = next(
            (pt for pt in project_tasks if pt.get("taskNumber") == task_info.get("taskNumber")),
            None,
        )
        if matching_task is not None:
            task_data = matching_task.get("taskLocation")

    report_numbers = [
        doc.get("axalantNummer")
        for doc in _extract_list(fetch_all_documents(task_id))
        if doc.get("axalantNummer") is not None
    ]
    technical_reports = [
        {"report": report_number, "download_link": fetch_report_download_link(report_number)}
        for report_number in report_numbers
    ]

    return {
        "task_id": task_id,
        "task_url": f"{BASE_URL_CAE_DB}{task_id}",
        "cae_number": task_info.get("taskNumber"),
        "task_name": task_info.get("thema"),
        "sub_tasks": sub_tasks_list,
        "linked_tasks": linked_tasks_list,
        "technical_reports": technical_reports,
        "task_data": task_data,
    }


def fetch_task_summaries_from_file(input_path):
    """Liest eine linked_tasks-JSON-Datei (search_linked_tasks.py-Output) und holt für jede enthaltene task_id die Task-Summary."""
    with open(input_path, "r", encoding="utf-8") as f:
        linked_tasks_data = json.load(f)

    task_summaries = []
    for task in linked_tasks_data.get("tasks", []):
        task_id = task.get("task_id")
        try:
            task_summaries.append(fetch_task_summary(task_id))
        except requests.exceptions.RequestException as exc:
            print(f"Warnung: task_summary für {task_id} fehlgeschlagen: {exc}")
    return task_summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Holt Task-Summaries für alle task_id-Einträge einer linked_tasks-JSON-Datei.")
    parser.add_argument("input_path", help="Pfad zur linked_tasks-JSON-Datei (search_linked_tasks.py-Output)")
    args = parser.parse_args()

    task_summaries = fetch_task_summaries_from_file(args.input_path)
    with open("task_summaries.json", "w", encoding="utf-8") as f:
        json.dump(task_summaries, f, indent=2, ensure_ascii=False)
    print(f"{len(task_summaries)} Task-Summaries geschrieben nach task_summaries.json")
