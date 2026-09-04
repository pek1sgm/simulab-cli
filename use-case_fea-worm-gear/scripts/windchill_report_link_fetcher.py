import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv('WINDCHILL_BASE_URL')
API_KEY = os.getenv('WINDCHILL_API_KEY')

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

input_file = "check_data_with_reports.json"
output_file = "check_data_with_reports_and_links.json"

# check_data.json laden
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Durch alle Einträge iterieren
for key, entry in data.items():
    calculation_report_number = entry.get("calculation_report_number")
    
    # Skip wenn calculation_report_number nicht vorhanden
    if not calculation_report_number:
        print(f"X {key}: Keine calculation_report_number vorhanden")
        continue
    
    try:
        # API-Request
        print(f"-- {key}: API-Request für {calculation_report_number}...", end=" ")
        response = requests.get(
            f"{BASE_URL}/guess_document",
            headers=headers,
            params={"report_number": calculation_report_number},
            timeout=10
        )
        
        # Response prüfen
        if response.status_code == 200:
            response_data = response.json()
            download_link = response_data.get("link_direct")
            
            if download_link:
                entry["calculation_report_download_link"] = download_link
                print(f"Ok! Link gefunden")
            else:
                print(f"Kein download_link in Response")
        else:
            print(f"HTTP {response.status_code}")
    
    except requests.exceptions.Timeout:
        print(f"Timeout")
    except requests.exceptions.RequestException as e:
        print(f"Fehler: {str(e)[:50]}")
    except json.JSONDecodeError:
        print(f"Ungültiges JSON in Response")
    except Exception as e:
        print(f"Fehler: {str(e)[:50]}")

# Aktualisierte Daten speichern
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n Ok! {output_file} aktualisiert")