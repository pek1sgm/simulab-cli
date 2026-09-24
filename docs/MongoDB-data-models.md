# MongoDB data models

**MonogDB Atlas**

[MongoDB Atlas Database](https://cloud.mongodb.com) is used in the simuLAB project to store metadata related to all simulation items which will be created with the SDM NG solution. Moreover, we will keep there information about pre-defined values for some metadata - such values are needed for proper validation.

Decision about using MongoDB can be found here: [07.02 - Data storage](https://inside-docupedia.bosch.com/confluence/spaces/simuLAB/pages/5002486834/07.02+-+Data+storage)

Description of all metadata can be found here: [Metadata definition](https://inside-docupedia.bosch.com/confluence/spaces/simuLAB/pages/5168902523/Metadata+definition)

**Table of Content**

- Metadata models
  - Pre-defined values
    - defaultMetadataValues collection
    - predefinedMetadataValues collection
    - groups collection
      - Indexes
  - SDM Management metadata schema
    - Schema version 1
    - Indexes
    - Schema validation rules
  - Users metadata schema
    - Indexes
  - Internal Relations metadata schema
    - Indexes
    - Schema validation rules
  - External Relations metadata schema
    - Indexes
    - Schema validation rules
  - Files metadata schema
    - Indexes
    - Schema validation rules

## Metadata models

> **Warning**
>
> Decision about below metadata model was made on January 24.

Each new version of the metadata schemas **have to** be documented here, so everyone will be aware of the changes in schema. When new schema version is introduced, such information should be provided:

1. List of changes in schema.
2. Date from which the scheme becomes effective.
3. Metadata schema in code block.

### Pre-defined values

These collections will be used for metadata validation. We will have three collections with pre-defined values:

1. **defaultMetadataValues** - values for metadata which will be updated by system admins (developers)
2. **predefinedMetadataValues** - values for metadata which will be updated by group admins (users with admin rights)
3. **groups** - collection of groups with metadata specific per group, like product and product type; can be updated by group admins (users with admin rights)

#### **defaultMetadataValues collection**

Only one document exist in this collection.

Changes:

1. **2025-04-16**: Add relationType to store types of relations used in internalRelations and externalRelations collection.
2. **2025-12-23** Add fileTag to store possible files tags used in to describe additionally files in files collection.
3. **2026-01-07**: Update status values based on the current status.
4. **2026-01-27**: Add **revisionConnectionType,** which will be used for internal relations for new revisions.
5. **2026-01-27**: Update relationType values to the current status.
6. **2026-04-02:** As only **report** will be supported for file tagging, only this value will be for now kept in database.

> **Info**
>
> According to the decision of January 24, **item type** will be not included in this collection as this metadata contain only two fixed values which should not change. **Item type** should be implemented as Enum in both, frontend and backend.

*defaultMetadataValues schema*

```py
{
 "_id": ObjectId,
 "status": [ str ],
 "retentionTime": [ str ],
 "relationType": [ str ],
 "fileTag": [ str ],
 "revisionConnectionType": str
}
```

| Param name | Current values |
| --- | --- |
| status | ["In Work", "Release"] |
| retentionTime | ["5 years", "2 years", "1 year", "1 month"] |
| `relationType` | ["simulationBox"] |
| fileTag | ["documentation", "report", "requirement"] (only **report** is kept in database) |
| revisionConnectionType | "createdFrom" |

#### **predefinedMetadataValues collection**

Only one document exist in this collection.

Values for this collection are taken from <https://sites.inside-share3.bosch.com/sites/120021/_layouts/15/WopiFrame2.aspx?sourcedoc=%7B2131C337-1ACB-45C1-8383-8788827BABCA%7D&file=simtool_simdomain_relations_mapping.xlsx&action=default&DefaultItemOpen=1>

Changes:

1. **2025-04-16**: Add connectionType to store types of existing relations connection types used in internalRelations and externalRelations collection.
2. **2025-04-24** Add sourceSystem to store external system names used in externalRelations.

*predefinedMetadataValues schema*

```py
{
 "_id":ObjectId,
 "domain": [ str ],
 "tool":
    {
 "tool_name1": [ str ],
 "tool_name2": [ str ]
    },
 "connectionType": [ str ],
    "sourceSystem": [ str ]
}
```

| Param name | Current values | Additional information |
| --- | --- | --- |
| domain | List of domains was taken from the knowledge graph database for P instance. |  |
| tool | List of tools (names and versions) was taken from the knowledge graph database for P instance. | Tools are kept as Object/dict, were key is the name of the tool and value is an array with all versions for this tool. |
| `connectionType` | List of internal and external connection types used for linking simulationBoxes, files, and external relations together |  |
| `sourceSystem` | List of external system names |  |
|  | List of possible file tags to set |  |

#### **groups collection**

Each group should have their own document in this collection.

Changes:

1. **2025-04-17** Added indexes on groupId, and productType attributes.
2. **2026-04-21** Compound index removed for **productType_1_groupId_1**

*groups schema*

```py
{
 "_id": ObjectId,
 "groupId": str,
 "productType":
    {
 "product_type1": [ str ],
 "product_tyep2": [ str ]
    }
}
```

##### Indexes

*groups indexes*

```py
db.groups.createIndex(
    {
        "groupId": 1
    },
    { unique: true }
)
```

| Param name | Current values | Additional information |
| --- | --- | --- |
| groupId | Name of the group. All groups were taken from the knowledge graph database for P instance. |  |
| productType | List of products. **No information about products per group in the current moment**. | Products are kept as Object/dict, were key is the product type and value is an array with products for this type. |

### SDM Management metadata schema

#### Schema version 1

**2025-02-20:** This is version in progress, we are still adding new parameters to the schema. Version 1 will be fixed when we will be closer to Q version deployment.

Changes:

1. **2025-01-29**: Change **sdmNumber**, **sdmRevision** and **sdmVersion** to Object and set _id as one of the keys in such Object. Such change was added to improve searching for the latest value of these parameters.
2. **2025-02-20**: Add **accessRights** param for access rights management.
3. **2025-03-14:** Change **projectNumber** type from **int** to **string** as this should be free text.
4. **2025-03-21:** Change **files** from a list of **"**filepath_1": "md-5 for 1" attributes, to the list of nested objects with required file attributes (which can extended in the future for more attributes)
5. **2025-04-11**: Change **sdmVersion** to Int32 as *Version* won't be an index in the db.
6. **2025-04-14**:
   - Change sdmVersion from Object to numeric type (int32). Reason: id of version exists already as main _id of the document,
   - Change owner to ntId - this attribute will be used in access management to find user documents together with accessRights
   - Decision to add indexes on following fields: sdmNumber.number together with sdmRevision.revision, owner, files._id together with _id, and all accessRights fields containg groupIds and ntIds.
   - Removed schemaVersion -  track changes in this document, in migration scripts, and mongoChangeLog collection. Having this attribute in every document cause unnecessary storage use, and it's not needed and used in application logic
7. **2025-04-18**: Change **retentionTime** to Int32 as the default unit used in Azure Retention Policies are days.
8. **2025-04-22**: Add **isLatest** as boolean to define whether version is the latest one among given sdmNumber and sdmRevision or not (for iFinder search purposes).
9. **2025-04-23**: Add **versionId** attribute to files attributes. **filePath** changed into **blobName**. **hash** changed into **contentMd5****.**
10. **2025-04-24:** Add **rbItem** object containing all attributes specific for migrated RB Items only. This object will exists only for migrated RB Item version 1, and than will be not populated to the next versions anymore.
11. **2025-05-05****:** Change **createdBy** and **lastModifiedBy** format to "Full Name (Department)". Such format is taken directly from JWT. Prefix like "EXTERNAL" and "FIXED-TERM" will be removed from user's full name before adding data to collection.
12. **2025-05-05:** Remove **files** attribute from sdmManagement schema. Files info will be stored in a separate **files** collection.
13. **2025-05-06:** NTID (**owner**) should be written in lower case letters
14. **2025-05-21: caeCustomer** and **caeEngineer** added to the schema (metadata from BSH group)
15. **2025-05-29: createdBy** and **lastModifiedBy** changed to **ntId** (should be written in lower case). Reason: we cannot relay on current personal data (even last name or first name can be changed, department is something what is regularly changed). The personal data should be displayed based on ntId from Users collection (fullName or different variant according to BUR decision)
16. **2025-06-27:** **caeCustomer** and **caeEngineer** changed to **ntId** (should be written in lower case).
17. **2025-07-23: rbItem** removed according to the latest statement
18. **2025-09-02:** **caeCustomer** and **caeEngineer** changed to arrays.
19. **2025-10-30: lock** added to lock/unlock document for edition.
20. **2025-12-18:** remove **retentionTime** from schema (it was removed some time ago).
21. **2026-02-06:** add **changeDescription** field to store information about the latest changes.
22. **2026-08-26:** add **isDeleted** and **deletionInfo** fields to schema. **deletionInfo** is an Object with two fields, **deletedAt** and **deletedBy.** All these fields are added only when item revision is deleted.

*sdmManagement schema*

```py
 "_id": ObjectId,
 "description": "Some description",
 "name": "Simulation item name",
 "status": "In Work",
 "owner": "pio2wz",  # NTID written in lower case letters
 "type": "Result",
 "createdBy": "pio2wz",  # NTID written in lower case letters
    "creationDate": "2025-03-06T14:29:23.024+00:00",
 "groupId": "ps-simulation",
 "isLatest": true,
 "lastModificationDate": "2025-03-06T14:29:23.024+00:00",
 "lastModifiedBy": "pio2wz",  # NTID written in lower case letters
    "projectNumber": "BM-00000000_000",
    "sdmNumber": {
 "_id": ObjectId,
 "number": "SDM0000001",
    },
 "sdmRevision": {
 "revision": "001",
 "_id": ObjectId,
    },
    "simulationTool": {
 "Ansys": [
            {"toolVersion": "2019R1", "toolSource": null},
            {"toolVersion": "2024R2", "toolSource": "source"},
        ],
 "Git": [{"toolVersion": "25.1", "toolSource": "ssh@git"}],
    },
    "sdmVersion": 1,
 "simulationDomain": ["Mechanics", "Acoustics"],
 "productType": "ESP/ABS",
 "tags": ["tag1", "tag2"],
 "product": "ESP",
    "accessRights": {
 "groupAccess": {"read": [""], "write": [""], "admin": [""]},
 "userAccess": {"read": [""], "write": [""], "admin": [""]},
    },
 "caeCustomer": ["pio2wz", "dop88wz"],  # NTID written in lower case letters, for BSH data
 "caeEngineer": ["pio2wz", "dop88wz"],  # NTID written in lower case letters, for BSH data
    "lock": { "lockedBy": "dop88wz", "lockedAt": "2025-10-30T14:29:23.024+00:00"},
 "changeDescription": "Updated metadata"
 "isDeleted": True # Added only when item is deleted
 "deletionInfo": { "deletedBy": "dop88wz", "deletedAt": "2025-10-30T14:29:23.024+00:00"},
}
```

#### Indexes

That's a first version from 17.04.2025 which will be extended/changed based on development needs.

1. **2025-07-15:** New index added for field *lastModificationDate* because of iFinder queries.
2. **2025-12-18:** Update index for sdmNumber.number and sdmRevision.revision with sdmVersion. Set index to unique.
3. **2026-04-21**: Removed userAccess and groupAccess indexes
4. **2026-06-19**: userAccess.read and userAccess.write indexes added

*sdmManagement indexes*

```py
db.sdmManagement.createIndex(
    {
        "sdmNumber.number": -1
    }
)

db.sdmManagement.createIndex(
    {
 "sdmNumber.number": 1,
 "sdmRevision.revision": 1,
 "sdmVersion": 1,
    },
    { unique: true }
)

db.sdmManagement.createIndex(
    {
        "owner": 1
    }
)

db.sdmManagement.createIndex(
    {
        "lastModificationDate": 1
    }
)

db.sdmManagement.createIndex(
    {
        "accessRights.userAccess.read": 1,
    }
)

db.sdmManagement.createIndex(
    {
        "accessRights.userAccess.write": 1,
    }
)
```

#### Schema validation rules

MongoDB setup:

1. Action: Error → return an error when invalid document will be inserted.
2. Level: Moderate → Apply validation rules to inserts and to updates on existing *valid* documents. Do not apply rules to updates on existing *invalid* documents.

Changes:

1. **2026-01-28:** Create schema validation rules and set them on all clusters (DEV, Q and PROD).
2. **2026-02-10:** Add **changeDescription** to validation rules as optional string field (as newly created item will not have this field).
3. **2026-08-26:**add **isDeleted** and **deletionInfo** fields to schema. **deletionInfo** is an Object with two fields, **deletedAt** and **deletedBy.**

*Schema validation rules*

```json
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
 '_id',
 'accessRights',
 'createdBy',
 'creationDate',
 'groupId',
 'isLatest',
 'lastModificationDate',
 'lastModifiedBy',
 'name',
 'owner',
 'sdmNumber',
 'sdmRevision',
 'sdmVersion',
 'status',
 'type'
    ],
    properties: {
      _id: {
        bsonType: 'objectId'
      },
      accessRights: {
        bsonType: 'object',
        properties: {
          groupAccess: {
            bsonType: 'object',
            properties: {
              admin: {
                bsonType: 'array',
                items: {
                  bsonType: 'string'
                }
              },
              read: {
                bsonType: 'array',
                items: {
                  bsonType: 'string'
                }
              },
              write: {
                bsonType: 'array',
                items: {
                  bsonType: 'string'
                }
              }
            },
            required: [
 'admin',
 'read',
 'write'
            ]
          },
          userAccess: {
            bsonType: 'object',
            additionalProperties: false,
            properties: {
              read: {
                bsonType: 'array',
                items: {
                  bsonType: 'string'
                }
              },
              write: {
                bsonType: 'array',
                items: {
                  bsonType: 'string'
                }
              }
            }
          }
        },
        required: [
 'groupAccess'
        ]
      },
      changeDescription: {
        bsonType: 'string'
      },
      createdBy: {
        bsonType: 'string'
      },
      creationDate: {
        bsonType: 'date'
      },
      description: {
        bsonType: 'string'
      },
      groupId: {
        bsonType: 'string'
      },
      isLatest: {
        bsonType: 'bool'
      },
      lastModificationDate: {
        bsonType: 'date'
      },
      lastModifiedBy: {
        bsonType: 'string'
      },
      lock: {
        bsonType: 'object',
        properties: {
          lockedAt: {
            bsonType: 'date'
          },
          lockedBy: {
            bsonType: 'string'
          }
        },
        required: [
 'lockedAt',
 'lockedBy'
        ]
      },
      name: {
        bsonType: 'string'
      },
      owner: {
        bsonType: 'string'
      },
      product: {
        bsonType: 'string'
      },
      productType: {
        bsonType: 'string'
      },
      projectNumber: {
        bsonType: 'string'
      },
      sdmNumber: {
        bsonType: 'object',
        properties: {
          _id: {
            bsonType: 'objectId'
          },
          number: {
            bsonType: 'string'
          }
        },
        required: [
 '_id',
 'number'
        ]
      },
      sdmRevision: {
        bsonType: 'object',
        properties: {
          _id: {
            bsonType: 'objectId'
          },
          revision: {
            bsonType: 'string'
          }
        },
        required: [
 '_id',
 'revision'
        ]
      },
      sdmVersion: {
        bsonType: 'int'
      },
      simulationDomain: {
        bsonType: 'array',
        items: {
          bsonType: 'string'
        }
      },
      simulationTool: {
        bsonType: 'object'
      },
      status: {
        bsonType: 'string'
      },
      tags: {
        bsonType: 'array',
        items: {
          bsonType: 'string'
        }
      },
      type: {
        bsonType: 'string'
      },
      uid: {
        bsonType: 'string'
      },
      isDeleted: {
        bsonType: 'bool'
      },
      deletionInfo: {
        bsonType: 'object',
        properties: {
          deletedAt: {
            bsonType: 'date'
          },
          deletedBy: {
            bsonType: 'string'
          }
        },
        required: [
 'deletedAt',
 'deletedBy'
        ]
      }
    },
    additionalProperties: false
  }
}
```

---

### Users metadata schema

Users metadata obtained from JWT token.

 Changes:

1. **2025-04-24**: Add **defaultGroupId** attribute to users collection.
2. **2025-05-06:** NTID (**ntId**) should be written in lower case letters
3. ~~**2025-12-11:** Add **validLicense** boolean attribute to users schema~~ (removed due to POs decision on sprint planning
4. **2026-06-15:** Add **createdSource, isLicensed, licensedSyncedAt** attributes

*users schema*

```
{
 "_id": ObjectId,
    "ntId": "dop88wz",    # NTID written in lower case letters
    "fullName": "Dobrowolski Piotr (BD/SWD-FSA7)",
    "email": "dop88wz@bosch.com",
    "createdAt": 2024-10-16T15:00:23.377+00:00,
 "defaultGroupId": "ps-simulation"
    "lastLoggedAt": 2025-10-16T15:00:23.377+00:00,
    "refreshToken": "hefkweflwemlgvfmwelvmwsdew5565levm",
 "isLicensed": true,
 "licensedSyncedAt": 2026-06-08T10:17:43.389+00:00,
 "createdSource": "license-sync" # created by license checker workflow if the user has never logged in
}
```

#### Indexes

*users indexes*

```
db.users.createIndex(
    {
        "ntId": 1
    },
    { unique: true }
)
```

---

### Internal Relations metadata schema

Relations between different simulation objects - simulation boxes, files, and external relations.

Changes:

1. **2025-04-24** After clarification from migration team, connectionType attribute moved to each relation object (connection type is always related to the connected resource type).
2. **2025-05-06:** NTID (**createdBy**) should be written in lower case letters.
3. **2025-05-15**: connectionType excluded from relation array - after final conclusion, the attribute will be common for the relation (according to the new semantics).
4. **2025-07-04**: lastModificationDate added to internal relation data model. This is needed for UI.
5. **2025-07-04:** Replace lastModificationDate with creationDate.
6. **2026-03-12:** depreciated added to the relation data model. This field is optional, used to mark outdated relations.
7. **2026-03-20:** add the new optional fields deprecationDate (UTC datetime) and deprecationUser (user's NTID) - to keep information who marked relation as deprecated.
8. **2026-03-23**: store information about deprecationDate and deprecationUser in a nested document under the names `onDate` and `byUser` .
9. **2026-04-21**: **relation.0.simulationBoxId_1** and **relation.1.simulationBoxId_1** indexes removed

*internalRelations schema*

```py
#Full schema
{
 "_id": ObjectId,
 "relation": [
        {
 "simulationBoxId": "67e69424922a82dd54c539aa",
 "type": "simulationBox/file/external",
 "fileId": "67e69424922a8ddd2dd54c539aa",
 "fileName": "file_name_1.txt",
 "externalRelationId": "67e69389922a82dd54c539a6"
        },
        {
 "simulationBoxId": "654656424922a82d54c539aa",
 "type": "simulationBox/file/external",
 "fileId": "67e69424922ssa8ddd2dd54c539aa",
 "fileName": "file_name_2.txt",
 "externalRelationId": "67e69389922a82dd54c539a6"
        }
    ],
 "connectionType": "CAE Target",
 "creationDate": "2025-03-06T14:29:23.024+00:00",
    "createdBy": "dop88wz",    # NTID written in lower case letters
 "deprecated":
    {
        "byUser": "dop88wz"    # NTID written in lower case letters
 "onDate": "2025-03-06T14:29:23.024+00:00",
    }
}

#Simulation Box to Simulation Box (valid for migration); First element of the list is Source , second is Target
{
 "_id": ObjectId,
 "relation": [
        {
 "simulationBoxId": "67e69424922a82dd54c539aa",
 "type": "simulationBox"
        },
        {
 "simulationBoxId": "654656424922a82d54c539aa",
 "type": "simulationBox"
        }
    ],
 "connectionType": "CAE Target",
 "creationDate": "2025-03-06T14:29:23.024+00:00",
    "createdBy": "dop88wz"    # NTID written in lower case letters
}

#Simulation Box to File; First element of the list is Source , second is Target
{
 "_id": ObjectId,
 "relation": [
        {
 "simulationBoxId": "67e69424922a82dd54c539aa",
 "type": "simulationBox"
        },
        {
 "simulationBoxId": "654656424922a82d54c539aa",
 "type": "file"
 "fileId": "67e69424922a8ddd2dd54c539aa",
 "fileName": "file_name.txt",
       }
    ],
 "connectionType": "CAE Target",
 "creationDate": "2025-03-06T14:29:23.024+00:00",
    "createdBy": "dop88wz"    # NTID written in lower case letters
}

#File to File; First element of the list is Source , second is Target
{
 "_id": ObjectId,
 "relation": [
        {
 "simulationBoxId": "67e69424922a82dd54c539aa",
            "type": "file",
 "fileId": "67e69424922a8ddd2dd54c539aa",
 "fileName": "file_name_1.txt"
        },
        {
 "simulationBoxId": "654656424922a82d54c539aa",
 "type": "file",
 "fileId": "67e69424922ssa8ddd2dd54c539aa",
 "fileName": "file_name_2.txt",
        }
    ],
 "connectionType": "CAE Target",
 "creationDate": "2025-03-06T14:29:23.024+00:00",
    "createdBy": "dop88wz"    # NTID written in lower case letters
}

#File to External
{
 "_id": ObjectId,
 "relation": [
        {
 "simulationBoxId": "67e69424922a82dd54c539aa",
            "type": "file",
 "fileId": "67e69424922a8ddd2dd54c539aa",
 "fileName": "file_name_1.txt"
        },
        {
 "type": "external",
 "externalRelationId": "67e69389922a82dd54c539a6"
        }
    ],
 "connectionType": "CAE Target",
 "creationDate": "2025-03-06T14:29:23.024+00:00",
    "createdBy": "dop88wz"    # NTID written in lower case letters
}
```

#### Indexes

*internalRelations indexes*

```py
db.internalRelations.relation.createIndex(
    {
        "simulationBoxId": 1
    }
)
```

#### Schema validation rules

MongoDB setup:

1. Action: Error → return an error when invalid document will be inserted.
2. Level: Moderate → Apply validation rules to inserts and to updates on existing *valid* documents. Do not apply rules to updates on existing *invalid* documents.

Changes:

1. **2026-01-28:** Create schema validation rules and set them on all clusters (DEV, Q and PROD).
2. **2026-03-05:** Remove **creationDate** from required fields - needed for upload existing of migrated items (otherwise it is not possible to update them).
3. **2026-03-20:** Add three new optional fields: deprecated, deprecationDate and deprecationUser. These fields will be added only when relation is marked as deprecated.
4. **2026-03-23**: Store information about deprecationDate and deprecationUser in a nested document under the names `onDate` and `byUser` .

*Schema validation rules*

```json
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
 '_id',
 'connectionType',
 'createdBy',
 'relation'
    ],
    properties: {
      _id: {
        bsonType: 'objectId'
      },
      connectionType: {
        bsonType: 'string'
      },
      createdBy: {
        bsonType: 'string'
      },
      creationDate: {
        bsonType: 'date'
      },
      deprecated: {
        bsonType: 'object',
        properties: {
          byUser: {
            bsonType: 'string'
          },
          onDate: {
            bsonType: 'date'
          }
        },
        required: [
 'byUser',
 'onDate'
        ]
      },
      relation: {
        bsonType: 'array',
        items: {
          bsonType: 'object',
          properties: {
            simulationBoxId: {
              bsonType: 'string'
            },
            type: {
              bsonType: 'string'
            }
          },
          required: [
 'simulationBoxId',
 'type'
          ]
        }
      }
    },
    additionalProperties: false
  }
}
```

---

### External Relations metadata schema

Metadata specific for external relations linked with simulation boxes and files

Changes:

1. **2025-04-24** New attribute sourceSystem added. Contains the value from predefinedMetadataValues.sourceSystem.
2. **2025-05-06:** NTID (**createdBy**) should be written in lower case letters.
3. **2025-05-09:** new version attribute added.
4. **2025-05-26:** objectId attribute added containing id of the linked object in external system.
5. **2025-07-04**: lastModificationDate added to internal relation data model. This is needed for UI.
6. **2025-07-04:** Replace lastModificationDate with creationDate.
7. **2026-03-12:** blobName and depreciated added to the relation data model. Both fields are optional.
8. **2026-03-20:** add the new optional fields deprecationDate (UTC datetime) and deprecationUser (user's NTID) - to keep information who marked relation as deprecated.
9. **2026-03-23**: Store information about deprecationDate and deprecationUser in a nested document under the names `onDate` and `byUser` .

*externalRelations schema*

```py
 {
 "_id": ObjectId,
    "simulationBoxId": "67e69424922a82dd54c539aa",
    "createdBy": "lfn1kor",    # NTID written in lower case letters
 "creationDate": "2025-03-06T14:29:23.024+00:00",
    "objectId": "566565656259265564612326",
 "connectionType": "CAE Target Relationship",
 "sourceSystem": "Teamcenter",
 "version": "1903",
    "link": "link1",
 "blobName":"0261B38289-01_003.psup"
    "deprecated": {
 "byUser": "dop88wz"    # NTID written in lower case letters
        "onDate": "2025-03-06T14:29:23.024+00:00",
    },
}
```

#### Indexes

*externalRelations indexes*

```py
db.externalRelations.createIndex(
    {
        "simulationBoxId": 1
    }
)
```

#### Schema validation rules

MongoDB setup:

1. Action: Error → return an error when invalid document will be inserted.
2. Level: Moderate → Apply validation rules to inserts and to updates on existing *valid* documents. Do not apply rules to updates on existing *invalid* documents.

Changes:

1. **2026-01-28:** Create schema validation rules and set them on all clusters (DEV, Q and PROD).
2. **2026-03-05:** Remove **creationDate** from required fields - needed for upload existing of migrated items (otherwise it is not possible to update them).
3. **2026-03-20:** Add three new optional fields: deprecated, deprecationDate and deprecationUser. These fields will be added only when relation is marked as deprecated.
4. **2026-03-23**: Store information about deprecationDate and deprecationUser in a nested document under the names `onDate` and `byUser` .

*Schema validation rules*

```json
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
 '_id',
 'connectionType',
 'createdBy',
 'objectId',
 'simulationBoxId',
 'sourceSystem'
    ],
    properties: {
      _id: {
        bsonType: 'objectId'
      },
      blobName: {
        bsonType: 'string'
      },
      connectionType: {
        bsonType: 'string'
      },
      createdBy: {
        bsonType: 'string'
      },
      creationDate: {
        bsonType: 'date'
      },
      deprecated: {
        bsonType: 'object',
        properties: {
          byUser: {
            bsonType: 'string'
          },
          onDate: {
            bsonType: 'date'
          }
        },
        required: [
 'byUser',
 'onDate'
        ]
      },
      link: {
        bsonType: 'string'
      },
      objectId: {
        bsonType: 'string'
      },
      simulationBoxId: {
        bsonType: 'string'
      },
      sourceSystem: {
        bsonType: 'string'
      },
      version: {
        bsonType: 'string'
      }
    },
    additionalProperties: false
  }
}
```

---

### Files metadata schema

Metadata related to files. It was created to be able to cover use cases with huge number of files  (>90 000) related to one simulation item (which causes significant JSON document file size increase which can exceed the limit of 16MB). Each file version in Azure Blob Storage should have its own document in this collection.
Size unit is `bytes.`

Changes:

1. **2025-05-05:** Decision to create **files** collection.
2. **2025-05-05: size** added as an additional attribute to the schema.
3. **2025-12-23: fileTag** added as an additional string attribute to the schema to describe file tag
4. **2026-04-21:** new compound index defined as recommended by Performance Advisor in MongoDB; **blobName** index created

*files schema*

```json
 {
 "_id": ObjectId,
    "simulationBoxId": "67e69424922a82dd54c539aa",
    "versionId": "string",
 "blobName": "test/blob_name_1",
 "contentMd5": "B6a4KWgaobH9DjW46dO4Tg=="
 "size": 100,
 "fileTag": "report"
}
```

#### Indexes

*files indexes*

```json
db.files.createIndex(
    {
        "simulationBoxId": 1,
        "_id": 1
    }
)db.files.createIndex(
    {
        "blobName": 1
    }
)
```

#### Schema validation rules

MongoDB setup:

1. Action: Error → return an error when invalid document will be inserted.
2. Level: Moderate → Apply validation rules to inserts and to updates on existing *valid* documents. Do not apply rules to updates on existing *invalid* documents.

Changes:

1. **2026-01-28:** Create schema validation rules and set them on all clusters (DEV, Q and PROD).
2. **2026-01-28:** **contentMd5** is not required because of issue with missing content-md5 in Azure Blob Storage side.

*Schema validation rules*

```json
{
  $jsonSchema: {
    bsonType: 'object',
    required: [
 '_id',
 'blobName',
 'simulationBoxId',
 'size',
 'versionId'
    ],
    properties: {
      _id: {
        bsonType: 'objectId'
      },
      blobName: {
        bsonType: 'string'
      },
      contentMd5: {
        bsonType: 'string'
      },
      fileTag: {
        bsonType: 'string'
      },
      simulationBoxId: {
        bsonType: 'string'
      },
      size: {
        bsonType: [
 'long',
 'int'
        ]
      },
      versionId: {
        bsonType: 'string'
      }
    },
    additionalProperties: false
  }
}
```
