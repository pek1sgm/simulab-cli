import os
import json
import re 
import ref_list

def compare_lists(list1, list2):
    return list(set(list1) - set(list2))

if __name__ == "__main__":
    # open registry file
    with open(os.path.join(os.path.dirname(__file__), '../data/bulk_upload_registry.json'), 'r') as f:
        data = json.load(f)

    # fetch all CAE numbers from the registry file
    cae_list = [cae for cae in data if re.match(r'CAE\d{6}', cae)]
    
    # print results
    print(f"{len(cae_list)} items found in bulk_upload_registry.json")
    print(f"List of CAE numbers: {cae_list}")
    print(f"{len(compare_lists(ref_list.cae_ref_list, cae_list))} items found in cae_ref_list but not in bulk_upload_registry.json")
    print(f"List of CAE numbers: {compare_lists(ref_list.cae_ref_list, cae_list)}")
