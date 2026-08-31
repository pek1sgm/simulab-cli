# download

- example call: simulabcli --instance QA -f download.json download
```json
{
  "sdm_number": "Your_SDM_Number",
  "sdm_revision": "Your_SDM_Revision",
  "download_directory": "Optional_Path_to_Download_Directory",
  "sdm_version": "Optional_SDM_Version",
  "filelist": [
    "Optional_Filename_1",
    "Optional_Filename_2"
  ],
  "access_token": "Optional_Access_Token"
}
```

# upload_directory

- example call: simulabcli --instance QA -f upload_directory.json upload_directory
```json
{
  "directory": "path/to/your/directory",
  "metadata": {
    "key1": "value1",
    "key2": "value2"
  },
  "existing_sdm_number": "your_sdm_number",
  "existing_sdm_revision": "your_sdm_revision",
  "ignore_list": [
    "*.log",
    "temp_files/"
  ],
  "access_token": "your_access_token"
}
```

# get_metadata

- example call: simulabcli --instance QA -f get_metadata.json get_metadata
```json
{
  "sdm_number": "Your_SDM_Number",
  "sdm_revision": "Your_SDM_Revision",
  "sdm_version": "Optional_SDM_Version",
  "access_token": "Optional_Access_Token"
}
```

# get_relations

- example call: simulabcli --instance QA -f get_relations.json get_relations
```json
{
  "sdm_number": "Your_SDM_Number",
  "sdm_revision": "Your_SDM_Revision",
  "access_token": "Optional_Access_Token"
}
```

