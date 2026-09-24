# SimulabCli API reference

> Quelle: https://pages.github.boschdevcloud.com/simuLAB/simulabCLI/latest/

## API reference

The simulab python package offers one main module named "cli" for automated interaction with the simulab server. Once you installed this package with "pip install simulabcli" you can use it within python programs. Just like with the package "requests", we designed our package to work best with direct import.

> **Example**
> ```python
> import simulabcli
> ```

We also ship a real command line interface that you can use in the terminal

> **Example**
> ```shell
> simulabcli -h
> ```

## instance

NO API: protected module to return the instance of the Simulab CLI so the corresponding endpoints can be used

### get_api_url()

Get the right api URL depending on the git branch. if there is not git branch (when installed from artifactory), the productive URL is returned.

**Raises:**

- `KeyError` – If the instance is not recognized.

### get_blob_url()

Get the right blob storage URL depending on the git branch. if there is not git branch (when installed from artifactory), the productive URL is returned.

**Raises:**

- `KeyError` – If the instance is not recognized.

### get_instance()

Get the current simuLAB instance based on the git branch. If there is no git branch (e.g., when installed from artifactory), the productive instance is returned.

### set_instance(instance)

Set whether to use file cache or runtime cache for access tokens.

## item schema

NO API: protected collection of Pydantic models for item management validation. These models are used as request and response models in item routers.

### ItemType

**Bases:** `str`, `Enum`

Enum class for item type. Item can only be one of these types.

### SdmDocumentIdentifier

**Bases:** `BaseModel`

Model for SDM item identifier.

### SdmManagementApiResponseParams

**Bases:** `SdmManagementBaseInputParams`

Model for for SDM Management metadata. Used to get params from REST API.

#### check_against_selectable_values(value, handler, ctx) `classmethod`

Validator to check if the value is in the selectable values from the API.

#### check_all_tools_are_simulation_tool_instances(value) `classmethod`

Validator to check if all items in the list are instances of SimulationTool.

#### from_api_response(data, access_token) `classmethod`

Create an instance of the class from the API response data.

#### from_file_or_dict_or_object(input_data, access_token) `classmethod`

Create an instance of the class from a file path, a dict or an object of the class.

#### from_json_file(file_path, access_token) `classmethod`

Create an instance of the class from a JSON file.

#### value_in_selectable_values(value, field_name, options) `classmethod`

Check if a value is in the selectable values.

### SdmManagementBaseInputParams

**Bases:** `BaseModel`

Base model for input params for SDM Management metadata. Should not be used directly, please use the daughter classes.

#### check_against_selectable_values(value, handler, ctx) `classmethod`

Validator to check if the value is in the selectable values from the API.

#### check_all_tools_are_simulation_tool_instances(value) `classmethod`

Validator to check if all items in the list are instances of SimulationTool.

#### from_api_response(data, access_token) `classmethod`

Create an instance of the class from the API response data.

#### from_file_or_dict_or_object(input_data, access_token) `classmethod`

Create an instance of the class from a file path, a dict or an object of the class.

#### from_json_file(file_path, access_token) `classmethod`

Create an instance of the class from a JSON file.

### SdmManagementInputParams

**Bases:** `SdmManagementBaseInputParams`

Model for input params for SDM Management metadata. Used for the upload of a new SDM item.

Pass access_token as context, e.g. by SdmManagementInputParams.model_validate(data, context={"access_token": token})

#### check_against_selectable_values(value, handler, ctx) `classmethod`

Validator to check if the value is in the selectable values from the API.

#### check_all_tools_are_simulation_tool_instances(value) `classmethod`

Validator to check if all items in the list are instances of SimulationTool.

#### from_api_response(data, access_token) `classmethod`

Create an instance of the class from the API response data.

#### from_file_or_dict_or_object(input_data, access_token) `classmethod`

Create an instance of the class from a file path, a dict or an object of the class.

#### from_json_file(file_path, access_token) `classmethod`

Create an instance of the class from a JSON file.

#### validate_group_id(value, info) `classmethod`

Validator to check if group id is in selectable values from the API.

#### validate_product_type(data, info) `classmethod`

Validator to check if product type is in selectable values from the API.

#### value_in_selectable_values(value, field_name, options) `classmethod`

Check if a value is in the selectable values.

### SdmManagementResponse

**Bases:** `BaseModel`

Response model for SDM Management metadata. Used only for responses from simuLAB REST API.

### SdmManagementUpdateParams

**Bases:** `SdmManagementBaseInputParams`

Model for update params for SDM Management metadata. Used for the update of an existing SDM item.

#### check_against_selectable_values(value, handler, ctx) `classmethod`

Validator to check if the value is in the selectable values from the API.

#### check_all_tools_are_simulation_tool_instances(value) `classmethod`

Validator to check if all items in the list are instances of SimulationTool.

#### from_api_response(data, access_token) `classmethod`

Create an instance of the class from the API response data.

#### from_file_or_dict_or_object(input_data, access_token) `classmethod`

Create an instance of the class from a file path, a dict or an object of the class.

#### from_json_file(file_path, access_token) `classmethod`

Create an instance of the class from a JSON file.

#### value_in_selectable_values(value, field_name, options) `classmethod`

Check if a value is in the selectable values.

### SimulationTool

**Bases:** `BaseModel`

Model for simulation tool. Pass access_token as context, e.g. by SimulationTool.model_validate(data, context={"access_token": token})

#### check_name_version(data, info) `classmethod`

Validator to check if name and version are in the selectable values from the API.

### get_selectable_values(access_token) `cached`

Get the selectable values for the metadata fields from the API. This function executes a GET request to the API endpoint.

## proxy

NO API: protected context manager to set proxy settings for Bosch network.

### BoschProxy

This context-class overwrites HTTP(S)_PROXY temporarily to allow access to login.microsoftonline. The original variables are restored when context is left. Patching of certificates is done platform dependently. Deactivate the adaption of proxy settings by setting environment variable "SIMULABCLI_DONT_TOUCH_PROXY" to non-empty Deactivate the call to patch_certifi by setting environment variable "SIMULABCLI_DONT_PATCH_CERTIFI" to non-empty

Example:: with BoschProxy(): cli.do_sth()

## requests

wrapper for the requests package to handle proxies and some standard settings

### delete(endpoint, access_token, params=None)

Wrapper for requests.delete with standard settings.

**Parameters:**

- `endpoint` (`str`) – The API endpoint to send the DELETE request to.
- `params` (`dict | None`, default: `None`) – The query parameters to send in the DELETE request.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

### get(endpoint, access_token, params=None)

Wrapper for requests.get with standard settings.

**Parameters:**

- `endpoint` (`str`) – The API endpoint to send the GET request to.
- `params` (`dict | None`, default: `None`) – The query parameters to send in the GET request.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

### http_error_handler(method)

Decorator to raise reasonable error messages for api calls

### post(endpoint, access_token, params=None, json=None)

Wrapper for requests.post with standard settings.

**Parameters:**

- `endpoint` (`str`) – The API endpoint to send the POST request to.
- `params` (`dict | None`, default: `None`) – The query parameters to send in the POST request.
- `json` (`dict | None`, default: `None`) – The JSON payload to send in the POST request.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

### put(endpoint, access_token, params=None, json=None)

Wrapper for requests.put with standard settings.

**Parameters:**

- `endpoint` (`str`) – The API endpoint to send the PUT request to.
- `params` (`dict | None`, default: `None`) – The query parameters to send in the PUT request.
- `json` (`dict | None`, default: `None`) – The JSON payload to send in the PUT request.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

## templates

definition of metadata templates for simulabcli commands

### get_create_external_relation_template(access_token, source_sdm_number='SDM0000000', source_sdm_revision='001')

Return template whose json representation demos the call: simulabcli get_metadata -f template.json

### get_create_internal_relation_template(access_token, source_sdm_number='SDM0000000', source_sdm_revision='001', target_sdm_number='SDM0000001', target_sdm_revision='001')

Return template whose json representation demos the call: simulabcli create_relations -f template.json

### get_create_revision_template(sdm_number='SDM0000000', sdm_revision='001', sdm_version=None, access_token=None)

Return template whose json representation demos the call: simulabcli create_revision -f template.json

### get_download_template(access_token, sdm_number='SDM0000000', sdm_revision='001', download_directory='path/to/download_directory')

Return template whose json representation demos the call: simulabcli download -f template.json

### get_list_files_template(sdm_number='SDM0000000', sdm_revision='001', sdm_version=None, access_token=None)

Return template whose json representation demos the call: simulabcli list_files -f template.json

**Parameters:**

- `sdm_number` (`str`, default: `'SDM0000000'`) – The item number. Defaults to "SDM0000000".
- `sdm_revision` (`str`, default: `'001'`) – The item revision. Defaults to "001".
- `sdm_version` (`int | None`, default: `None`) – The version of the item. Defaults to None.
- `access_token` (`str | None`, default: `None`) – Access token for authentication. If None, the function will use the default access token.

**Returns:**

- `dict` (`dict`) – Template to be used for list_files command.

### get_metadata_template(access_token, sdm_number='SDM0000000', sdm_revision='001', sdm_version=None)

Return template whose json representation demos the call: simulabcli get_metadata -f template.json

### get_relations_template(access_token, sdm_number='SDM0000000', sdm_revision='001')

Return template whose json representation demos the call: simulabcli get_relations -f template.json

### get_revisions_template(sdm_number='SDM0000000', access_token=None)

Return template whose json representation demos the call: simulabcli get_revisions -f template.json

### get_upload_directory_template(access_token)

Return template whose json representation demos the call: simulabcli upload_directory -f template.json

### get_upload_existing_directory_template(access_token, existing_sdm_number='SDM0000000', existing_sdm_revision='001', directory=UPLOAD_DIRECTORY_PATH)

Return template whose json representation demos the call: simulabcli upload_list -f template.json

### get_upload_existing_list_template(access_token, existing_sdm_number='SDM0000000', existing_sdm_revision='001', directory=UPLOAD_DIRECTORY_PATH, file1=UPLOAD_FILE1_PATH, file2=UPLOAD_FILE2_PATH)

Return template whose json representation demos the call: simulabcli upload_list_existing -f template.json

### get_upload_list_template(access_token)

Return template whose json representation demos the call: simulabcli upload_list -f template.json

### get_versions_template(sdm_number='SDM0000000', sdm_revision='001', access_token=None)

Return template whose json representation demos the call: simulabcli get_versions -f template.json

### write_template_files(access_token=None)

writes all templates to the current working directory with predefined file names

## token

module for token handling module for simulabcli.

> **Tipp: stick to only a few function!**
>
> Utilize use_file_cache(True/False) to allow or disable caching on the disk.
>
> Utilize get_access_token().get_current() to obtain a JWT token for passing to the cli functions

### AccessToken

**Bases:** `ABC`

work around using Desktop app (interactive login) redirect_uri="http://localhost"

#### \_\_init\_\_()

if store_as_file is True, the access token will be stored in a keyfile on the disk. Otherwise, the token is only kept inside the runtime object. Usecase: web apps may not write to disk.

#### create_public_client()

Create a public client application for MSAL.

#### digest_key_content(public_client, key_content)

Helper function to digest the key content (e.g. from file) into the local variable self.current_access_token.

#### get_current() `abstractmethod`

don't call this directly, use child class implementation

### CachedAccessToken

**Bases:** `AccessToken`

We do not expect to have many variations of AccessToken, so I use inheritance instead of decorator patterns. the cache (with defined protocol load/dump protocol) is injected into the constructor.

#### \_\_init\_\_(cache)

either pass file-cache or a runtime-cache object

#### create_public_client()

Create a public client application for MSAL.

#### digest_key_content(public_client, key_content)

Helper function to digest the key content (e.g. from file) into the local variable self.current_access_token.

#### get_current()

template method to get current access token depending on child class implementation of _for_local_user.

### FileCache

Token cache stored in a file.

#### dump(content)

Store the content in a file cache.

#### load()

Return the content from the file cache, cf. self.keyfile for filename.

### RuntimeCache

Token cache stored in runtime memory only.

#### dump(content)

Store the content in the runtime cache.

#### load()

Return the content from the runtime cache.

### get_access_token()

Get the access token, either from file cache or runtime cache.

### get_auth_header(access_token)

Get the authorization header for HTTP requests.

### obfuscate_access_token(access_token)

Obfuscate the access token for logging purposes.

### use_file_cache(flag)

Set whether to use file cache or runtime cache for access tokens.

## type aliases

Common type hints aliases.

### DirectoryType = Path | str | None `module-attribute`

A path to the directory where the files are located. If the files are not in a directory, this argument can be None.

### FilesType = list[str | Path | BytesIO] `module-attribute`

A list of file paths, strings, or BytesIO objects.

### MetadataType = dict | SdmManagementInputParams | SdmManagementUpdateParams | Path `module-attribute`

Item metadata provided as dict, pydantic model, or path to JSON file.

## utils

NO API: protected utilities for interacting with the Simulab REST API and Azure Blob Storage.

This module provides functions to authenticate with the Simulab API, manage metadata in MongoDB, and upload/download files to/from Azure Blob Storage.

### LockContextManager

Context manager to lock an item during a block of code.

### add_blob_data_to_mongodb(item, access_token)

Function to add the blob data to the MongoDB. This is needed to update the file info kept in the mongodb about an item.

**Parameters:**

- `item` (`SdmManagementResponse`) – The object containing item ID and revision.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

### check_item_lock(simulation_box_id, access_token)

Function to check if a simulation box is locked.

**Parameters:**

- `simulation_box_id` (`str`) – The simulation box ID.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

**Raises:**

- `RuntimeError` – If the simulation box is locked.

**Returns:**

- `bool` (`bool`) – True if item is locked, False otherwise.

### check_latest_version(simulation_box_id, access_token)

Function to check if the given simulation box ID corresponds to the latest version.

**Parameters:**

- `simulation_box_id` (`str`) – The simulation box ID.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

**Returns:**

- `bool` (`bool`) – True if the simulation box is the latest version, False otherwise.

### create_container(item, access_token)

Checks if the metadata is in mongoDB and creates a container in the Azure Blob Storage.

**Parameters:**

- `item` (`SdmManagementResponse`) – The object containing item ID and revision.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

**Returns:**

- `bool` (`bool`) – True if the container was created, False otherwise.

### create_external_relation(box_id, connection_type, external_system, external_id, access_token, external_version=None, external_link=None)

Function to create an external relation for a simulation box. Args: box_id (str): The simulation box ID. connection_type (str): The type of connection. external_system (str): The external system name. external_id (str, optional): The external ID. Defaults to None. external_version (str, optional): The external version. Defaults to None. external_link (str, optional): The external link. Defaults to None. Returns: response (dict): The response from the API.

### create_internal_relation(box_id, related_box_id, connection_type, access_token=None)

Function to create an internal relation between two simulation boxes.

**Parameters:**

- `box_id` (`str`) – The simulation box ID.
- `related_box_id` (`str`) – The related simulation box ID.
- `connection_type` (`str`) – The type of connection.
- `access_token` (`str`, default: `None`) – Access token for authentication.Defaults to None.

Returns: response (dict): The response from the API.

### create_new_revision(simulation_box_id, change_description, access_token)

Function to create a new revision of a simulation box.

**Parameters:**

- `simulation_box_id` (`str`) – The simulation box ID.
- `change_description` (`str`) – The change description for the new revision. Must be between 1 and 100 characters.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

**Returns:**

- `SdmManagementResponse` (`SdmManagementResponse`) – The response from the API containing the new revision details.

### download_file_from_blob_storage(sas_token, item_id, blob_name, version_id, download_directory=None)

Download a file from Azure Blob Storage using a SAS token.

**Parameters:**

- `sas_token` (`str`) – The SAS token for the Azure Blob Storage.
- `item_id` (`str`) – The item ID. Must be of the form 'SDM-'.
- `blob_name` (`str`) – The name of the blob in the container.
- `version_id` (`str`) – The version ID of the blob to download.
- `download_directory` (`Path`, default: `None`) – The local path to save the downloaded file.

### get_blob_name(file, directory=None)

helper function to get the desired blob name for a given file

### get_changed_and_added_files(existing_file_info, files_to_upload, directory=None)

Function to get the dict of files with their md5sum which are new or changed compared to the existing file info.

**Parameters:**

- `existing_file_info` (`list[dict]`) – List of dictionaries containing file path, size in bytes and md5-sum of the existing files in the simulation box.
- `files_to_upload` (`FilesType`) – List of file paths to be uploaded.
- `directory` (`DirectoryType`, default: `None`) – The base directory for the files to be uploaded. If provided, the file paths will be relative to this directory. Defaults to None.

**Returns:**

- `dict` (`dict`) – dict with all the file paths which have changed and their corresponding md5-sum.

### get_file_info_for_item(box_id, access_token)

Get file information (name, size, md5-sum) for all files in a simulation box.

**Parameters:**

- `box_id` (`str`) – The 24-digit box ID.

**Returns:**

- `list[dict]` – list[dict]: List of dictionaries containing file path, size in bytes and md5-sum

### get_file_info_for_item_from_blob(item_id, sas_token)

Get a list of files in the Azure Blob Storage container.

**Parameters:**

- `item_id` (`str`) – The item ID. Must be of the form 'SDM-'.
- `sas_token` (`str`) – The SAS token for the Azure Blob Storage.

**Returns:**

- `list[str]` – list[str]: List of file names in the container.

### get_file_md5(file)

helper function to get the md5-sum of a file or file-like object

### get_files_in_upload_directory(directory, ignore_list)

Function to get all files in a directory that are not in the ignore list.

**Parameters:**

- `directory` (`str | Path`) – Path to the directory.
- `ignore_list` (`list[str]`) – List of ignore patterns.

Returns: list[str]: List of file paths.

### get_item_size_for_download(item_id, sas_token)

Get the total size of all files in the Azure Blob Storage container.

**Parameters:**

- `item_id` (`str`) – The item ID. Must be of the form 'SDM-'.
- `sas_token` (`str`) – The SAS token for the Azure Blob Storage.

**Returns:**

- `size` (`int`) – The total size of all files in the container in bytes.

### get_item_size_for_upload(filelist)

Function to get the total size of all files in the list (on local storage) for the upload.

**Parameters:**

- `filelist` (`list or dict`) – List of file paths or file_likes or dict with file paths or file_likes and their md5-sum.

Returns: int: The total size of all files in bytes.

### get_meta_data_from_mongo_db(item, access_token)

Function to get the metadata from the MongoDB.

**Parameters:**

- `item` (`SdmManagementResponse`) – The object containing item ID and revision.

Returns: dict: The metadata from the MongoDB.

### get_predefined_values(access_token)

Get the predefined values for the relations fields from the API. This function executes a GET request to the API endpoint.

### get_relations_from_mongo_db(box_id, access_token=None)

Function to get the relations of a simulation box from the MongoDB.

**Parameters:**

- `box_id` (`str`) – The simulation box ID.
- `access_token` (`str`, default: `None`) – Access token for authentication. Defaults to None.

Returns: dict: Relations of the simulation box.

### get_sas_token(container_name, access_token, item_size=0)

Get a SAS token for a container from the REST API.

**Parameters:**

- `container_name` (`str`) – Container name.
- `item_size` (`int`, default: `0`) – Size of the item in bytes (sum of all file sizes). Defaults to 0.
- `access_token` (`str`) – Access token. If not provided,

**Returns:**

- `str` (`str`) – SAS token.

### get_updated_metadata(new_metadata, existing_metadata, access_token)

Function to update the metadata of an item with new values.

**Parameters:**

- `new_metadata` (`SdmManagementInputParams`) – The new metadata to be used for the update. Fields which are missing, empty or None will not be updated
- `existing_metadata` (`SdmManagementUpdateParams`) – The existing metadata to be updated.

Returns: SdmManagementUpdateParams: The updated metadata.

### is_empty_directory(path_str)

Check if provided directory path is empty.

**Parameters:**

- `path_str` (`str`) – Directory path.

**Returns:**

- `bool` (`bool`) – True if the directory is empty, False otherwise.

### is_valid_directory(path_str)

Check if provided string is a valid directory path.

**Parameters:**

- `path_str` (`str`) – Directory path.

**Returns:**

- `bool` (`bool`) – True if the path exists and is a directory, False otherwise.

### open_file_like(file_like, \*args, \*\*kwargs)

An adapter-function: this context manager falls back to standard python's: with open(...) as f: However, for file-like objects like io.BytesIO, the open-function must not be called, but the file-like object is returned. This helper allows to deal with strings|Path objects and BytesIO-objects in the same manner.

### remove_ignored_files_from_list(files, ignore_list)

Function to remove files from a list that are in an ignore list using .gitignore rules.

**Parameters:**

- `files` (`list[str]`) – List of file paths.
- `ignore_list` (`list[str]`) – List of ignore patterns.

Returns: list[str]: List of file paths without the ignored

### remove_item_lock(simulation_box_id, access_token)

Function to remove the lock from a simulation box.

**Parameters:**

- `simulation_box_id` (`str`) – The simulation box ID.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

### sdm_number2box_id(sdm_number, sdm_revision, sdm_version, access_token)

Function to get the simulation box ID from the item number and revision. Args: sdm_number (str): The item number. sdm_revision (str): The item revision. sdm_version (int): The version of the metadata schema. Default is 1. Returns: str: The simulation box ID.

### sdm_number_to_pydantic(sdm_number, sdm_revision, sdm_version)

Helper function to convert a sdm_number and sdm_revision to a pydantic model which is used internally to talk to simuLAB API endpoints.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `sdm_version` (`int | None`) – The item version.

**Returns:**

- `SdmDocumentIdentifier` (`SdmDocumentIdentifier`) – Pydantic model which is used internally to talk to simuLAB API endpoints.

### send_meta_data_to_mongo_db(item_metadata, access_token, will_upload_files)

Function to create the necessary metadata in the MongoDB and return a item ID and revision.

**Parameters:**

- `item_metadata` (`SdmManagementInputParams`) – The metadata to be created in the MongoDB.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.
- `will_upload_files` (`bool`) – Whether any files will be uploaded or not.

**Returns:**

- `SdmManagementResponse` (`SdmManagementResponse`) – The response from the MongoDB containing created item ID and revision.

### set_item_lock(simulation_box_id, access_token)

Function to set a lock on a simulation box.

**Parameters:**

- `simulation_box_id` (`str`) – The simulation box ID.
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

### update_metadata_in_mongo_db_by_box_id(box_id, updated_metadata, access_token, copy_files)

Function to update the metadata of an item in the MongoDB when simulation box ID is provided.

**Parameters:**

- `box_id` (`str`) – The 24-digit box ID.
- `updated_metadata` (`SdmManagementUpdateParams`) – The updated metadata to be sent to the MongoDB.
- `copy_files` (`bool`) – Whether any files changed in the update (copy_files = False) or not (copy_files = True).
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

**Returns:**

- `SdmManagementResponse` (`SdmManagementResponse`) – The response from the MongoDB containing updated item ID and revision.

### update_metadata_in_mongo_db_by_sdm_number_revision(sdm_number_revision, updated_metadata, access_token, copy_files)

Function to update the metadata of an item in the MongoDB when SDM number and revision is provided.

**Parameters:**

- `sdm_number_revision` (`str`) – The item number and revision in the format 'SDM-'.
- `updated_metadata` (`SdmManagementUpdateParams`) – The updated metadata to be sent to the MongoDB.
- `copy_files` (`bool`) – Whether any files changed in the update (copy_files = False) or not (copy_files = True).
- `access_token` (`str | None`) – The access token for authentication. If None, token will be obtained from cache or login.

**Returns:**

- `SdmManagementResponse` (`SdmManagementResponse`) – The response from the MongoDB containing updated item ID and revision.

### upload_file_to_blob_storage(sas_token, item_id, file_like, md5sum, blob_name)

Upload a file to Azure Blob Storage using a SAS token.

**Parameters:**

- `sas_token` (`str`) – The SAS token for the Azure Blob Storage.
- `item_id` (`str`) – The item ID. Must be of the form 'SDM-'.
- `file_like` (`str | Path`) – The local path to the file to be uploaded.
- `md5sum` (`str`) – The MD5 checksum of the file to be uploaded.
- `blob_name` (`str`) – The name of the blob in the container.

### upload_multiple_files_to_blob_storage(item_id, files, sas_token, directory=None)

Upload all specified files to the Azure Blob storage.

**Parameters:**

- `item_id` (`str`) – The item ID. Must be of the form 'SDM-'.
- `files` (`FilesType`) – List of file (or file-likes) or dict with file (or file-likes) and their md5-sum.
- `sas_token` (`str`) – The SAS token for the Azure Blob Storage.
- `directory` (`str | Path`, default: `None`) – The base directory for the files.

### validate_change_description(change_description)

Validate change description: - must be between 1 and 100 characters, - empty strings are not allowed (i.e. only spaces).

**Parameters:**

- `change_description` (`str`) – Description of the reason for the change.

**Raises:**

- `ValueError` – When change description does not meet validation requirements.

### validate_connection_type(connection_type, access_token=None)

get the connection types from the API and validate the given connection type

### write_item_metadata_json(sdm_number, sdm_revision, download_directory, access_token, sdm_version)

Function to write the metadata of an item to a JSON file.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `download_directory` (`str | Path`) – The directory where the JSON file will be saved as simulab_metadata.json

## Cli

public API: Command line interface for simulab.

Provides functions to upload and download files to/from the Bosch simuLAB SDM as well as to create relations between items and to read metadata and relations.

Public methods:

- upload_directory: Uploads a directory to the SDM with given metadata. Can also upload to an existing item if specified.
- upload_list: Uploads a list of files to the SDM with given metadata.
- upload_list_to_existing_item: Uploads a list of files to an existing SDM item with given metadata updates.
- download: Downloads files from the SDM to a given directory.
- create_relation: Creates a relation between two SDM items or between an SDM item and an external entity.
- get_metadata: Retrieves metadata of a given SDM item.
- list_files: Lists files in a given SDM item.

> **Hinweis**
>
> turn to reference of _token.py for authentication and token management.

Links:

- MongoDB data models
- Swagger documentation: q-system

### DEFAULT_IGNORE_LIST = ['\*.key', '\*-protokoll.txt'] `module-attribute`

the ignore list helps avoid uploading crazy file types like *-protokoll.txt which only exists on HPC

### create_relation(connection_type, source_sdm_number, source_sdm_revision, source_sdm_version=None, target_sdm_number=None, target_sdm_revision=None, target_sdm_version=None, external_system=None, external_id=None, external_version=None, external_link=None, internal=True, access_token=None)

Function to create a relation between two Bosch simuLAB SDM items or between an SDM item and an external entity.

**Parameters:**

- `connection_type` (`str`) – The type of the connection. Must be a valid simuLAB connection type.
- `source_sdm_number` (`str`) – The item number of the source item.
- `source_sdm_revision` (`str`) – The item revision of the source item.
- `source_sdm_version` (`int`, default: `None`) – The version of the metadata schema for the source item. Default is 1.
- `target_sdm_number` (`str`, default: `None`) – The item number of the target item. If None, an external entity is assumed.
- `target_sdm_revision` (`str`, default: `None`) – The item revision of the target item. If None, an external entity is assumed.
- `target_sdm_version` (`int`, default: `None`) – The version of the metadata schema for the target item. Default is 1.
- `external_system` (`str`, default: `None`) – The external system of the external entity. Must be
- `external_id` (`str`, default: `None`) – The external ID of the external entity. Must be provided if internal is False.
- `external_version` (`str`, default: `None`) – The external version of the external entity.
- `external_link` (`str`, default: `None`) – The web link of the external entity.
- `internal` (`bool`, default: `True`) – If True, creates an internal relation between two SDM items. If False, creates a relation to an external entity.
- `access_token` (`str`, default: `None`) – Access token for authentication. If None, the function will use the default access token.

### create_revision(changeDescription, sdm_number, sdm_revision, sdm_version=None, access_token=None)

Function to create a new revision of an item in the Bosch simuLAB SDM.

**Parameters:**

- `changeDescription` (`str`) – The change description for the new revision. Must not be empty or longer than 100 characters.
- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `sdm_version` (`int | None`, default: `None`) – The version of the metadata schema. Default is the latest version.
- `access_token` (`str | None`, default: `None`) – Access token for authentication. If None, the function will use interactive authentication in the browser to get an access token.

**Returns:**

- `dict` (`dict`) – Information about the created revision.

### download(sdm_number, sdm_revision, download_directory=None, \*, sdm_version=None, filelist=None, access_token=None)

Function to download a whole item or single files from the Bosch simuLAB SDM.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `sdm_version` (`int`, default: `None`) – The version of the metadata schema. Default is the latest version.
- `download_directory` (`str`, default: `None`) – The directory where the files will be downloaded. If None is provided, the files will be handled in memory only.
- `filelist` (`list[str]`, default: `None`) – List of files to be downloaded. If None, all files will be downloaded.
- `access_token` (`str`, default: `None`) – Access token for authentication. If None, the function will use the default access token.

**Returns:**

- `list[str]` – List[str]: List of downloaded file paths or blob names.
- `Dict` (`dict`) – Dict of downloaded file paths.
- `Dict` (`dict`) – Dict of downloaded file metadata.

### get_metadata(sdm_number, sdm_revision, sdm_version=None, access_token=None)

Function to get metadata of a Bosch simuLAB SDM item.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `sdm_version` (`int`, default: `None`) – The version of the metadata schema. Default is the latest version.
- `access_token` (`str`, default: `None`) – Access token for authentication. If None, the function will use the default access token.

**Returns:**

- `dict` – Metadata of the item.

### get_relations(sdm_number, sdm_revision, sdm_version=None, access_token=None)

Function to get relations of a Bosch simuLAB SDM item. Args: sdm_number (str): The item number. sdm_revision (str): The item revision. sdm_version (int): The version of the metadata schema. Default is the latest version. access_token (str): Access token for authentication. If None, the function will use the default access token. Returns: dict: Relations of the item.

### get_revisions(sdm_number, access_token=None)

Function to get the revisions and versions of an item from the Bosch simuLAB SDM.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `access_token` (`str`, default: `None`) – Access token for authentication. Defaults to None.

Returns: dict: Revisions and versions of the item.

### get_versions(sdm_number, sdm_revision, access_token=None)

Function to get the versions of an item revision from the Bosch simuLAB SDM.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `access_token` (`str`, default: `None`) – Access token for authentication. Defaults to None.

Returns: dict: Versions of the item.

### list_files(sdm_number, sdm_revision, sdm_version=None, access_token=None, include_version_info=False)

Function to list files in a Bosch simuLAB SDM container.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `sdm_version` (`int | None`, default: `None`) – The version of the metadata schema. Default is the latest version
- `access_token` (`str | None`, default: `None`) – Access token for authentication. If None, the function will use the default access token.

**Returns:**

- `dict` (`dict`) – dict of files in the item with version info and md5 hashes.

### main()

Main function for the command line interface.

### upload_directory(directory, metadata, existing_sdm_number=None, existing_sdm_revision=None, ignore_list=None, access_token=None)

Function to be used by the user to upload a directory to the Bosch simuLAB SDM. If an existing item is specified an upload to the existing item is performed.

**Parameters:**

- `directory` (`str`) – Path to the directory to be uploaded.
- `metadata` (`dict | SdmManagementInputParams | SdmManagementUpdateParams | Path`) – Metadata for the item. If a new item is created, the metadata must be complete. If an existing item is specified, only the fields to be updated need to be provided.
- `existing_sdm_number` (`str`, default: `None`) – The item number of an existing item.
- `existing_sdm_revision` (`str`, default: `None`) – The item revision of an existing item.
- `ignore_list` (`list[str]`, default: `None`) – List of ignore patterns. Files in the directory which match the pattern will not be uploaded. If not specified, the program uses the internal DEFAULT_IGNORE_LIST avoid e.g. secret key-files.
- `access_token` (`str`, default: `None`) – Access token for authentication. If None, the function will use the default access token.

**Raises:**

- `ValueError` – When directory path is invalid or directory is empty.

**Returns:**

- `SdmManagementResponse` – an object containing the created item ID and revision.

### upload_list(files, metadata, \*, directory=None, access_token=None)

Function to be used by the user to upload a directory to the Bosch simuLAB SDM.

**Parameters:**

- `files` (`FilesType`) – sth iterable. The items must be (subclass) of BytesIO or a string/Path-object
- `metadata` (`MetadataType`) – dict or SdmManagementInputParams or Path to json-file (we pass it to utils.input2pydantic)
- `directory` (`DirectoryType`, default: `None`) – ignore this input if you call upload_list directly. It's a helper for upload_directory, which falls back to this function to avoid code duplication
- `access_token` (`str | None`, default: `None`) – Access token for authentication. If None, we request one from simuLAB-API

**Returns:**

- `dict` – Information about newly created simulation item.

### upload_list_to_existing_item(sdm_number, sdm_revision, files, metadata, directory=None, access_token=None)

Function to upload files to an existing Bosch simuLAB SDM item.

**Parameters:**

- `sdm_number` (`str`) – The item number.
- `sdm_revision` (`str`) – The item revision.
- `files` (`FilesType`) – List of files to be uploaded. The items must be (subclass) of BytesIO or a string/Path-object.
- `metadata` (`MetadataType`) – Metadata for the item. Does not need to be complete, only the fields to be updated.
- `directory` (`DirectoryType`, default: `None`) – Path to the directory where the files are located. If the files are not in a directory, this argument can be None.
- `access_token` (`str`, default: `None`) – Access token for authentication. If None, the function will use the default access token.

Returns: dict: Information about the uploaded item.
