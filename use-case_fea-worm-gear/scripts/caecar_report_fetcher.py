import caecar
import json


# Create a GraphQLQuery client for reuse during the application runtime.
caecar_client = caecar.GraphQLQuery(auth=caecar.CaecarAuth())


def cae_list(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return list(data.keys())


def _normalize_variants(variants):
    normalized_variants = []

    if isinstance(variants, dict):
        iterable = variants.items()
        for variant_name, variant_data in iterable:
            if not isinstance(variant_data, dict):
                continue
            item = {"name": variant_name, **variant_data}
            item.pop("calculation_report_number", None)
            normalized_variants.append(item)
        return normalized_variants

    if isinstance(variants, list):
        for variant_data in variants:
            if not isinstance(variant_data, dict):
                continue
            item = dict(variant_data)
            item.pop("calculation_report_number", None)
            if "name" not in item:
                continue
            normalized_variants.append(item)

    return normalized_variants


# define query. We can use multi-line strings and format the query nicely.
cae_numbers = cae_list("check_data.json")
if not cae_numbers:
    raise ValueError("Keine CAE-Nummern in check_data.json gefunden.")

input_file = "check_data.json"
output_file = "check_data_with_reports.json"

# Build a GraphQL-compatible list like: ["CAE1", "CAE2"].
cae_numbers_gql = ", ".join(f'\"{cae}\"' for cae in cae_numbers)
query = f"""query{{
  report(
    match: {{task: {{cae_number: {{in: [{cae_numbers_gql}]}}}}}}
  ) {{
    calculation_report_number
    task {{
      cae_number
    }}
  }}
}}"""

# Execute the query
data = caecar_client.query_data(query, 'caedb')

# Write JSON with only cae_number and calculation_report_number.
if isinstance(data, list):
    reports = data
elif isinstance(data, dict):
    reports = data.get("report")
    if reports is None:
        nested_data = data.get("data", {})
        if isinstance(nested_data, dict):
            reports = nested_data.get("report")
    if reports is None:
        reports = []
else:
    reports = []

result = [
    {
        "cae_number": report.get("task", {}).get("cae_number"),
        "calculation_report_number": report.get("calculation_report_number"),
    }
    for report in reports
    if isinstance(report, dict)
]

with open("query_results.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

# Build CAE -> calculation_report_number mapping.
report_number_by_cae = {
    entry.get("cae_number"): entry.get("calculation_report_number")
    for entry in result
    if entry.get("cae_number")
}

# Update check_data.json in place.
with open(input_file, encoding="utf-8") as f:
    check_data = json.load(f)

for cae_number, cae_data in check_data.items():
    if not isinstance(cae_data, dict):
        continue

    cae_data["variants"] = _normalize_variants(cae_data.get("variants", []))

    report_number = report_number_by_cae.get(cae_number)
    if report_number is None:
        continue

    cae_data["calculation_report_number"] = report_number

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(check_data, f, indent=2, ensure_ascii=False)
