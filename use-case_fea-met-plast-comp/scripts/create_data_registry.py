import caecar
import requests
from pathlib import Path
from dotenv import load_dotenv
import re
import json
import os

# import environment variables from .env
load_dotenv()

# Bosch-interne CA in certifi einpatchen, damit die HTTPS-Verbindung zum Vault verifiziert.
try:
    from boschcertifi import patch_certifi

    patch_certifi()
except Exception:
    pass

FOLDER_PATH = os.getenv("FOLDER_PATH")
BASE_URL = os.getenv("WINDCHILL_BASE_URL")

# Vault-Zugang (Bootstrap) aus .env - kann nicht selbst aus dem Vault kommen.
VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_NAMESPACE = os.getenv("VAULT_NAMESPACE")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
VAULT_CACERT = os.getenv("VAULT_CACERT")


def get_vault_secret(mount, path, field, kv_version=2):
    """Liest ein einzelnes Feld eines KV-Secrets aus dem OpenBao/Vault
    (mount/path/field wie in vault.csv, z. B. 'prod', 'caePortalUrl',
    'windchillAuthKey')."""
    if not (VAULT_ADDR and VAULT_TOKEN):
        raise SystemExit("VAULT_ADDR und VAULT_TOKEN muessen in der .env gesetzt sein.")
    mount = mount if mount.endswith("/") else mount + "/"
    api = f"{mount}data/{path}" if kv_version == 2 else f"{mount}{path}"
    response = requests.get(
        f"{VAULT_ADDR.rstrip('/')}/v1/{api}",
        headers={"X-Vault-Token": VAULT_TOKEN, "X-Vault-Namespace": VAULT_NAMESPACE},
        verify=VAULT_CACERT or True,
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()["data"]
    data = body["data"] if kv_version == 2 else body
    if field not in data:
        raise KeyError(f"Feld '{field}' nicht in {mount}{path} gefunden.")
    return data[field]


# WINDCHILL_API_KEY kommt jetzt aus dem Vault (prod/caePortalUrl -> windchillAuthKey).
API_KEY = get_vault_secret("prod", "caePortalUrl", "windchillAuthKey")

CAEDB_URL_TEMPLATE = "https://rb-wam.bosch.com/caedb/#/aufgabeUebersicht/{id}"

output_file = Path(__file__).resolve().parent / "data" / "data_registry.json"

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
caecar_client = caecar.GraphQLQuery(auth=caecar.CaecarAuth())

# Function that fetches the download link for a given calculation report number
def get_report_download_link(calculation_report_number):
    try:
        response = requests.get(
            f"{BASE_URL}/guess_document",
            headers=headers,
            params={"report_number": calculation_report_number},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("link_direct")

    except (requests.exceptions.RequestException, json.JSONDecodeError) as error:
        print(f"Fehler bei {calculation_report_number}: {error}")
        return None

# Function that makes a graphQL query to fetch calculation report number and download link for a given CAE id
def report_query(cae_id):
    query = f"""query{{
        report(match: {{task_id: {{eq: {cae_id}}}}}) {{calculation_report_number}}}}"""
    calculation_report_number = caecar_client.query_data(query, 'caedb')
    if calculation_report_number:
        calculation_report_number = calculation_report_number[0]['calculation_report_number']
        download_link = get_report_download_link(calculation_report_number)
        return calculation_report_number, download_link
    return None, None

# Function that makes a graphQL query to fetch task IDs for a given CAE number
def cae_no_query(cae_no):
    query = f"""query{{
        task_all(match: {{cae_number: {{eq: "{cae_no}"}}}}) {{id}}}}"""
    cae_id = caecar_client.query_data(query, 'caedb')
    if cae_id:
        cae_id = cae_id[0]['id']
        calculation_report_number, download_link = report_query(cae_id)
        cae_url = CAEDB_URL_TEMPLATE.format(id=cae_id)
        return cae_url, calculation_report_number, download_link
    return None

if __name__ == "__main__":
    data_registry = []
    cae_list = [] 
    for name in os.listdir(FOLDER_PATH):
        path = os.path.join(FOLDER_PATH, name)
        if os.path.isdir(path):
            match = re.search(r"CAE(\d+)", path)
            if match:
                cae_no = match.group(0)
                cae_url, calculation_report_number, download_link = cae_no_query(cae_no)
                cae_list.append(cae_no)
                data_registry.append({"cae-no.": cae_no,
                                    "task_name": name,
                                    "path": path,
                                    "cae_url": cae_url,
                                    "calculation_report_number": calculation_report_number,
                                    "download_link": download_link})
        
    # write data_registry into a json file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data_registry, f, indent=4, ensure_ascii=False)

