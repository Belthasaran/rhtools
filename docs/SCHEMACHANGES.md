# Database Schema Changes Log

## Purpose
This document tracks all database schema changes made to the rhtools project databases (rhdata.db and patchbin.db) as required by project rules.

---

## 2025-10-12: Upload Status Tracking Table (patchbin.db)

### Date
October 12, 2025

### Description
Added `upload_status` table to `patchbin.db` to track which blob files have been uploaded to various cloud storage providers (IPFS, Arweave, ArDrive, etc.).

### Rationale
- **Multi-Provider Support**: Track uploads across multiple storage providers independently
- **Deduplication**: Avoid re-uploading files that are already available
- **Metadata Storage**: Store provider-specific identifiers (CIDs, transaction IDs, file IDs)
- **Audit Trail**: Maintain timestamps of when files were uploaded
- **Extensibility**: Support additional providers without schema changes

### Tables/Columns Affected

**Database**: `patchbin.db`

**New Table**: `upload_status`

**Columns**:
1. `file_name` (TEXT PRIMARY KEY)
   - References blob file name from attachments table
   - Format: pblob_GAMEID_HASH or rblob_GAMEID_HASH
   
2. `uploaded_ipfs` (INTEGER DEFAULT 0)
   - Boolean flag: 1 = uploaded to IPFS, 0 = not uploaded
   
3. `uploaded_arweave` (INTEGER DEFAULT 0)
   - Boolean flag: 1 = uploaded to Arweave, 0 = not uploaded
   
4. `uploaded_ardrive` (INTEGER DEFAULT 0)
   - Boolean flag: 1 = uploaded to ArDrive, 0 = not uploaded
   
5. `ipfs_uploaded_time` (TIMESTAMP NULL)
   - When file was uploaded to IPFS
   
6. `arweave_uploaded_time` (TIMESTAMP NULL)
   - When file was uploaded to Arweave
   
7. `ardrive_uploaded_time` (TIMESTAMP NULL)
   - When file was uploaded to ArDrive
   
8. `ipfs_cid` (TEXT NULL)
   - IPFS Content Identifier (CIDv1)
   
9. `arweave_txid` (TEXT NULL)
   - Arweave transaction ID
   
10. `ardrive_file_id` (TEXT NULL)
    - ArDrive file ID
    
11. `notes` (TEXT NULL)
    - Additional metadata or custom provider info
    
12. `created_time` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    - When record was created
    
13. `updated_time` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    - When record was last updated

### Data Type Changes
None - new table

### Constraints
- PRIMARY KEY on `file_name`
- ON CONFLICT(file_name) DO UPDATE support for upsert operations

### Related Scripts
- `list-unuploaded-blobs.js` - Lists files not yet uploaded
- `mark-upload-done.js` - Marks files as uploaded

### Documentation
- `docs/UPLOAD_TRACKING.md` - Complete upload tracking documentation
- Table auto-created by scripts on first run

---

## 2025-10-12: Local Resource Tracking Fields (Migration 004)

### Date
October 12, 2025

### Description
Added three new columns to the `gameversions` table to support intelligent change detection and versioned ZIP file storage for Phase 2 of updategames.js implementation.

### Rationale
- **Efficiency**: Enable HTTP HEAD requests to check if files changed before downloading (saves bandwidth)
- **Versioning**: Preserve old ZIP file versions when games are updated (zips/GAMEID_VERSION.zip pattern)
- **Deduplication**: Prevent duplicate downloads and storage of identical files
- **Tracking**: Maintain HTTP metadata (ETag, Last-Modified) for accurate change detection

### Tables/Columns Affected

**Table**: `gameversions`

**New Columns**:
1. `local_resource_etag` (VARCHAR 255)
   - Stores HTTP ETag header from download response
   - Used for efficient change detection
   - NULL if server doesn't provide ETag

2. `local_resource_lastmodified` (TIMESTAMP)
   - Stores HTTP Last-Modified header from download response
   - Alternative change detection method
   - NULL if server doesn't provide Last-Modified

3. `local_resource_filename` (VARCHAR 500)
   - Stores local filesystem path where ZIP was saved
   - Format: zips/GAMEID.zip (v1) or zips/GAMEID_VERSION.zip (v2+)
   - Always populated when file is downloaded

**Indexes Created**:
- `idx_gameversions_local_filename` on `local_resource_filename`
- `idx_gameversions_local_etag` on `local_resource_etag`

### Data Type Changes
None - all new columns

### Constraints
None - all columns nullable

### Migration File
`electron/sql/migrations/004_add_local_resource_tracking.sql`

### Computed Columns Classification
These fields are classified as **COMPUTED COLUMNS** and must not be updated from external JSON imports:
- `local_resource_etag`
- `local_resource_lastmodified`
- `local_resource_filename`

Also previously classified as computed:
- `combinedtype` (computed from other fields)
- `gvimport_time` (database auto-generated)
- `version` (database auto-incremented)
- `gvuuid` (database auto-generated)

**Requirement**: Scripts importing JSON data (loaddata.js, updategames.js) must exclude these fields from JSON imports.

### Documentation
- `docs/LOCAL_RESOURCE_TRACKING.md` - Complete feature documentation
- `docs/NEW_UPDATE_SCRIPT_PHASE2_SPEC.md` - Phase 2 specification (updated)
- `docs/GAMEVERSIONS_TABLE_SCHEMA.md` - Updated with new fields

---

## 2025-01-10: Locked Attributes System (Migration 003)

### Date
January 10, 2025

### Description
Added `legacy_type` column and implemented locked attributes system

### Rationale
Allow curators to set manual classifications that persist across version updates without being overwritten by external data imports.

### Tables/Columns Affected

**Table**: `gameversions`

**New Column**:
- `legacy_type` (VARCHAR 255)
  - User-curated type classification
  - Locked attribute - preserved across versions
  - NULL by default, set manually by curators

### Migration File
Manual ALTER TABLE (documented in previous schema changes)

### Documentation
- `docs/LOCKED_ATTRIBUTES.md`
- `docs/GV_LOCKED_ATTRIBUTES_IMPLEMENTATION.md`

---

## 2025-01-10: Combined Type Field (Migration 002)

### Date
January 10, 2025

### Description
Added `combinedtype` computed column that combines all type and difficulty fields into a single human-readable string.

### Rationale
- Simplify display of complete type/difficulty information
- Enable efficient filtering by combined classification
- Support search across all type indicators in single field

### Tables/Columns Affected

**Table**: `gameversions`

**New Column**:
- `combinedtype` (VARCHAR 255)
  - Computed from: fields_type, difficulty, raw_difficulty, raw_fields.type
  - Format: "[fields_type]: [difficulty] (raw_difficulty) (raw_fields.type)"
  - Example: "Kaizo: Advanced (diff_4) (kaizo)"

**Index Created**:
- `idx_gameversions_combinedtype` on `combinedtype`

### Migration File
`electron/sql/migrations/002_add_combinedtype.sql`

### Backfill
`electron/sql/migrations/003_backfill_combinedtype.js` - Backfilled 2,913 existing records

### Documentation
- `docs/GV_COMBINEDTYPE_UPDATE.md`
- `docs/MIGRATION_003_BACKFILL_COMBINEDTYPE.md`

---

## 2025-01-10: New Schema Fields Support (Migration 001)

### Date
January 10, 2025

### Description
Added support for new JSON schema format from SMWC with nested type and difficulty fields.

### Rationale
- Support new JSON schema from external data sources
- Extract more granular type/difficulty information
- Maintain backward compatibility with old format

### Tables/Columns Affected

**Table**: `gameversions`

**New Columns**:
1. `fields_type` (VARCHAR 255)
   - Extracted from `fields.type` in new JSON format
   - More specific type classification
   - NULL for old format data

2. `raw_difficulty` (VARCHAR 255)
   - Extracted from `raw_fields.difficulty`
   - Raw difficulty code (diff_1 through diff_6)
   - NULL for old format data

**Indexes Created**:
- `idx_gameversions_fields_type` on `fields_type`
- `idx_gameversions_raw_difficulty` on `raw_difficulty`

### Data Type Changes
None - all new columns

### Migration File
`electron/sql/migrations/001_add_fields_type_raw_difficulty.sql`

### Code Changes
- Updated `loaddata.js` with field extraction logic
- Added boolean normalization (true→"1", false→"0")

### Documentation
- `docs/GV_SCHEMA_UPDATE_SUMMARY.md`
- `docs/GV_BUGFIX_LOADDATA.md`

---

## Original Schema (Pre-2025)

### Description
Initial `gameversions` table with core fields for game metadata, authorship, difficulty, and patch references.

### Core Fields
- gvuuid (primary key)
- gameid, version (unique constraint)
- name, author, authors
- gametype, difficulty
- description, tags
- download_url, url
- patchblob1_name, pat_sha224
- gvjsondata (full JSON backup)
- gvimport_time

### Documentation
- Original `electron/sql/rhdata.sql`

---

## Summary of All Schema Changes

| Date | Migration | Changes | Reason |
|------|-----------|---------|--------|
| Pre-2025 | Initial | Original schema | Core functionality |
| 2025-01-10 | 001 | fields_type, raw_difficulty | New JSON schema support |
| 2025-01-10 | 002 | combinedtype | Computed type display |
| 2025-01-10 | 003 | legacy_type | Locked attributes |
| 2025-10-12 | 004 | local_resource_* (3 fields) | Resource tracking & versioning |

**Total New Columns**: 7  
**Total New Indexes**: 6  
**Migrations Created**: 4  
**Backfill Scripts**: 1

---

## Migration Status

| Migration | File | Status | Records Affected |
|-----------|------|--------|------------------|
| 001 | 001_add_fields_type_raw_difficulty.sql | ✅ Complete | All (nullable) |
| 002 | 002_add_combinedtype.sql | ✅ Complete | All (nullable) |
| 003 | 003_backfill_combinedtype.js | ✅ Complete | 2,913 backfilled |
| 004 | 004_add_local_resource_tracking.sql | ✅ Ready | N/A (new feature) |

---

## Applying Migrations

### Complete Migration Sequence

```bash
# From project root
cd /home/main/proj/rhtools

# 001: New schema fields
sqlite3 electron/rhdata.db < electron/sql/migrations/001_add_fields_type_raw_difficulty.sql

# 002: Combined type
sqlite3 electron/rhdata.db < electron/sql/migrations/002_add_combinedtype.sql

# 003: Backfill combinedtype (optional, for existing data)
node electron/sql/migrations/003_backfill_combinedtype.js

# 004: Local resource tracking
sqlite3 electron/rhdata.db < electron/sql/migrations/004_add_local_resource_tracking.sql
```

### Verification

```bash
# Check schema
sqlite3 electron/rhdata.db "PRAGMA table_info(gameversions);" | grep -E "fields_type|raw_difficulty|combinedtype|legacy_type|local_resource"

# Expected output shows all 7 new columns:
# 34|fields_type|VARCHAR(255)|0||0
# 35|legacy_type|VARCHAR(255)|0||0
# 36|raw_difficulty|VARCHAR(255)|0||0
# 37|combinedtype|VARCHAR(255)|0||0
# 38|local_resource_etag|VARCHAR(255)|0||0
# 39|local_resource_lastmodified|TIMESTAMP|0||0
# 40|local_resource_filename|VARCHAR(500)|0||0
```

---

## Related Documentation

- **Schema Reference**: `docs/GAMEVERSIONS_TABLE_SCHEMA.md` - Complete field documentation
- **Locked Attributes**: `docs/LOCKED_ATTRIBUTES.md` - Locked attributes guide
- **Resource Tracking**: `docs/LOCAL_RESOURCE_TRACKING.md` - local_resource_* fields guide
- **Phase 2 Spec**: `docs/NEW_UPDATE_SCRIPT_PHASE2_SPEC.md` - Change detection specification

---

## 2025-10-12: User Annotations Tables (clientdata.db)

### Date
October 12, 2025

### Description
Added three new tables to `clientdata.db` for storing user-specific annotations for games and stages, including ratings, status tracking, notes, and stage metadata.

### Rationale
- **User Privacy**: Each user maintains their own ratings and notes in their local clientdata.db
- **Stage-Level Tracking**: Support per-stage ratings and notes for games with documented stages
- **Progress Tracking**: Track game completion status (Default/In Progress/Finished)
- **Flexible Organization**: Hidden flag for organizing personal game library
- **Rating System**: 1-5 difficulty rating scale at both game and stage level

### Tables/Columns Affected

**Database**: `clientdata.db`

#### New Table: `user_game_annotations`

**Purpose**: Store user-specific data for each game

**Columns**:
1. `gameid` (VARCHAR 255 PRIMARY KEY)
   - References gameid from rhdata.db gameversions table
   
2. `status` (VARCHAR 50 DEFAULT 'Default')
   - User's progress status: 'Default', 'In Progress', 'Finished'
   
3. `user_rating` (INTEGER)
   - User's personal difficulty rating (1-5 scale)
   - NULL if not rated
   - CHECK constraint: (user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5))
   
4. `hidden` (INTEGER DEFAULT 0)
   - Boolean flag: 0 = visible, 1 = hidden from main list
   
5. `user_notes` (TEXT)
   - User's personal notes about the game
   
6. `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
   - When annotation was created
   
7. `updated_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
   - When annotation was last modified

**Indexes**:
- `idx_user_game_status` ON status
- `idx_user_game_hidden` ON hidden
- `idx_user_game_rating` ON user_rating

**Triggers**:
- `trigger_user_game_updated` - Auto-updates updated_at on modification

#### New Table: `game_stages`

**Purpose**: Store stage/exit metadata for games

**Columns**:
1. `stage_key` (VARCHAR 510 PRIMARY KEY)
   - Format: "gameid-exitnumber" (e.g., "12345-01")
   
2. `gameid` (VARCHAR 255 NOT NULL)
   - References the game
   
3. `exit_number` (VARCHAR 255 NOT NULL)
   - Stage/exit number (e.g., "0x01", "1", "105")
   
4. `description` (TEXT)
   - Stage description/name
   
5. `public_rating` (DECIMAL(3,2))
   - Community average rating for this stage
   
6. `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
7. `updated_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

**Indexes**:
- `idx_game_stages_gameid` ON gameid
- `idx_game_stages_exit` ON exit_number

**Constraints**:
- UNIQUE(gameid, exit_number)

**Triggers**:
- `trigger_game_stages_updated` - Auto-updates updated_at on modification

#### New Table: `user_stage_annotations`

**Purpose**: Store user-specific annotations for individual stages

**Columns**:
1. `stage_key` (VARCHAR 510 PRIMARY KEY)
   - Format: "gameid-exitnumber"
   
2. `gameid` (VARCHAR 255 NOT NULL)
   - References the game
   
3. `exit_number` (VARCHAR 255 NOT NULL)
   - References the specific stage
   
4. `user_rating` (INTEGER)
   - User's personal difficulty rating for this stage (1-5)
   - NULL if not rated
   - CHECK constraint: (user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5))
   
5. `user_notes` (TEXT)
   - User's personal notes about this stage
   
6. `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
7. `updated_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

**Indexes**:
- `idx_user_stage_gameid` ON gameid
- `idx_user_stage_rating` ON user_rating

**Constraints**:
- UNIQUE(gameid, exit_number)

**Triggers**:
- `trigger_user_stage_updated` - Auto-updates updated_at on modification

#### New Views

**v_games_with_annotations**:
- Convenience view for querying games with user annotations
- Includes all fields from user_game_annotations
- Uses COALESCE for default values

**v_stages_with_annotations**:
- Convenience view joining game_stages with user_stage_annotations
- Shows both stage metadata and user annotations
- LEFT JOIN preserves stages without user annotations

### Data Type Changes
None - all new tables

### Migration File
`electron/sql/migrations/001_clientdata_user_annotations.sql`

### Related Files Updated
- `electron/sql/clientdata.sql` - Updated with new schema for fresh installs

### Usage Notes

**Rating Scale**: 1-5 where:
- 1 = Very Easy
- 2 = Easy  
- 3 = Normal
- 4 = Hard
- 5 = Very Hard
- NULL = Not rated

**Status Values**:
- 'Default' - Not started or no status set
- 'In Progress' - Currently playing
- 'Finished' - Completed

**Stage Keys**: Format is "gameid-exitnumber"
- Examples: "12345-01", "9999-0xFF", "test-105"
- Ensures unique identification across games

**Important**: 
- Not all games have documented stages - the stage tables are optional
- Each user should have their own clientdata.db
- This database should NOT be synced or shared between users
- Scripts should support CLIENTDATA_DB_PATH environment variable

### Documentation
- Migration script: `electron/sql/migrations/001_clientdata_user_annotations.sql`
- Commands: `docs/DBMIGRATE.md` (updated)
- This file: `docs/SCHEMACHANGES.md` (this entry)

---

*Last Updated: October 12, 2025*  
*Next Migration: TBD*
