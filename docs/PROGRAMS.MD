# Programs and Utilities

This document lists all interactive programs and utilities in the rhtools project that can be invoked as scripts.

---

## Main Programs

### updategames.js
**Purpose**: Main script to update game database from SMWC

**Usage**:
```bash
node updategames.js [options]
```

**Key Options**:
- `--game-ids=<ids>` - Process specific game IDs only
- `--all-patches` - Process all patches, not just primary
- `--dry-run` - Preview changes without modifying database
- `--resume` - Resume from interrupted run
- `--use-js-blobs` - Use JavaScript blob creator (default: Python)

**Documentation**: See `docs/UPDATEGAMES_*.md` files

---

## Blob Management

### list-unuploaded-blobs.js
**Purpose**: List blob files that haven't been uploaded to cloud providers

**Usage**:
```bash
node list-unuploaded-blobs.js [options]
```

**Key Options**:
- `--provider=<name>` - Check provider (ipfs, arweave, ardrive, all)
- `--create-archive` - Create ZIP of unuploaded files
- `--scan-ipfs` - Check IPFS gateway availability
- `--scan-ardrive=<folder>` - Scan ArDrive folder
- `--output=<file>` - Save list to file

**Examples**:
```bash
# List unuploaded to Arweave
node list-unuploaded-blobs.js

# Create archive for IPFS upload
node list-unuploaded-blobs.js --provider=ipfs --create-archive

# Check IPFS and list missing
node list-unuploaded-blobs.js --provider=ipfs --scan-ipfs --verbose
```

**Documentation**: Auto-creates `upload_status` table in `patchbin.db`

---

### mark-upload-done.js
**Purpose**: Mark blob files as uploaded to a provider

**Usage**:
```bash
node mark-upload-done.js --provider=<name> [files...]
node mark-upload-done.js --provider=<name> --file=<list.txt>
cat files.txt | node mark-upload-done.js --provider=<name> --stdin
```

**Key Options**:
- `--provider=<name>` - Provider name (required)
- `--file=<path>` - Read file names from file
- `--stdin` - Read from stdin
- `--txid=<id>` - Arweave transaction ID
- `--cid=<cid>` - IPFS CID
- `--dry-run` - Preview without updating

**Examples**:
```bash
# Mark specific files
node mark-upload-done.js --provider=ipfs pblob_123.bin pblob_456.bin

# Mark from list
node mark-upload-done.js --provider=arweave --file=uploaded.txt

# Mark from stdin
cat uploaded.txt | node mark-upload-done.js --provider=ipfs --stdin

# With metadata
node mark-upload-done.js --provider=arweave --txid=abc123 pblob_123.bin
```

**Documentation**: Updates `upload_status` table in `patchbin.db`

---

### reprocess-attachments.js
**Purpose**: Reprocess attachments for existing game versions

**Usage**:
```bash
node reprocess-attachments.js --game-ids=<ids> [options]
```

**Key Options**:
- `--game-ids=<ids>` - Game IDs to reprocess (required)
- `--all-patches` - Process all patches
- `--dry-run` - Preview without changes

**Use Case**: Fix attachments with missing decoded fields without deleting gameversions

**Documentation**: See `docs/UPDATEGAMES_DECODER_001.md`

---

## Verification Tools

### verify-all-blobs.js
**Purpose**: Verify blob integrity (JavaScript version)

**Usage**:
```bash
node verify-all-blobs.js [options]
```

**Key Options**:
- `--verify-blobs=<source>` - Source: 'db' or 'files'
- `--gameid=<id>` - Verify specific game
- `--file-name=<name>` - Verify specific blob
- `--full-check` - Test with flips
- `--verify-result` - Verify result hash
- `--newer-than=<value>` - Only verify recent blobs
- `--log-file=<path>` - Log results

**Examples**:
```bash
# Basic verification
node verify-all-blobs.js

# Full check with result verification
node verify-all-blobs.js --full-check --verify-result

# Verify recent blobs only
node verify-all-blobs.js --newer-than="2025-10-12"

# Verify from database
node verify-all-blobs.js --verify-blobs=db
```

**Documentation**: See `docs/VERIFICATION_TOOLS.md`

---

### verify-all-blobs.py
**Purpose**: Verify blob integrity (Python version)

**Usage**:
```bash
python3 verify-all-blobs.py [options]
```

**Key Options**:
- `--dbtype=<type>` - Database: 'sqlite' or 'rhmd'
- `--verify-blobs=<source>` - Source: 'db' or 'files'
- `--gameid=<id>` - Verify specific game
- `--full-check` - Test with flips
- `--verify-result` - Verify result hash
- `--newer-than=<value>` - Only verify recent blobs

**Examples**:
```bash
# Verify SQLite database
python3 verify-all-blobs.py --dbtype=sqlite

# Verify RHMD file
python3 verify-all-blobs.py --dbtype=rhmd

# Full check with result verification
python3 verify-all-blobs.py --full-check --verify-result
```

**Documentation**: See `docs/VERIFICATION_TOOLS.md`

---

## Data Management

### loadsm.js
**Purpose**: JavaScript utility for loading hack data including blob decoding

**Usage**: Typically used as a library, but can be invoked directly

**Features**:
- Blob decoding (JavaScript and Python-created blobs)
- LZMA decompression
- Hash verification

**Documentation**: Compatible with both JavaScript and Python blob formats

---

### backfill_rhmd.js
**Purpose**: Export data from SQLite database to Python RHMD file format

**Usage**:
```bash
node backfill_rhmd.js
```

**Use Case**: Maintain compatibility with Python scripts by exporting to RHMD format

**Documentation**: See `docs/PYTHON_COMPATIBILITY_GUIDE.md`

---

## Utilities

### identify-incompatible-keys.js
**Purpose**: Audit database for incompatible encryption key formats

**Usage**:
```bash
node identify-incompatible-keys.js
```

**Use Case**: Find blobs with keys that need format conversion

**Documentation**: See `docs/UPDATEGAMES_DECODER_001.md`

---

## Python Utilities

### blob_crypto.py
**Purpose**: Standalone Python library for blob encryption/decryption

**Usage**:
```bash
# Encrypt
python3 blob_crypto.py encrypt <input_file> <output_file> <key>

# Decrypt
python3 blob_crypto.py decrypt <input_file> <key> <expected_hash> <output_file>

# Generate key
python3 blob_crypto.py generate-key
```

**Features**:
- PBKDF2HMAC key derivation
- Fernet encryption/decryption
- Auto-detection of blob formats
- Compatible with JavaScript-created blobs

**Documentation**: See `docs/PYTHON_COMPATIBILITY_GUIDE.md`

---

### create_blob_python.py
**Purpose**: Create blobs using Python (called by blob-creator.js)

**Usage**:
```bash
python3 create_blob_python.py <patch_file> <gameid> <blobs_dir> <pat_sha224> [result_file]
```

**Use Case**: Ensure universal compatibility by creating blobs in Python format

---

### loadsmwrh_compat.py
**Purpose**: Compatibility wrapper for loadsmwrh.py

**Use Case**: Allow Python scripts to work with JavaScript-created blobs

**Documentation**: See `docs/PYTHON_COMPATIBILITY_GUIDE.md`

---

## Testing

### tests/test_blob_compatibility.js
**Purpose**: Test blob format compatibility

**Usage**:
```bash
node tests/test_blob_compatibility.js
# or
npm run test:blob-compat
```

**What it tests**:
- JavaScript blob creation
- Decoding by record-creator.js
- Decoding by loadsm.js
- Decoding by blob_crypto.py
- Key format compatibility
- Python-created blob compatibility

---

### tests/test_python_script_compat.js
**Purpose**: Test integration with Python scripts

**Usage**:
```bash
node tests/test_python_script_compat.js
# or
npm run test:python-compat
```

**What it tests**:
- blob_crypto.py decryption
- loadsmwrh_compat.py wrapper
- RHMD export
- Python decoding of exported metadata

---

## NPM Scripts

Convenient aliases for common operations:

```bash
# Testing
npm run test:blob-compat          # Blob compatibility tests
npm run test:python-compat         # Python script compatibility tests

# Verification
npm run verify:blobs               # Verify from files
npm run verify:blobs-db            # Verify from database
npm run verify:blobs-full          # Full check with flips
npm run verify:blobs-result        # Full check with result verification

# Utilities
npm run utils:identify-keys        # Identify incompatible keys
npm run utils:reprocess-attachments # Reprocess attachments
npm run utils:backfill-rhmd        # Backfill RHMD file
```

---

## Database Schema

### Migration Scripts

Located in `electron/sql/migrations/`:
- `001_add_fields_type_raw_difficulty.sql`
- `002_add_combinedtype.sql`
- `003_backfill_combinedtype.js`
- `004_add_local_resource_tracking.sql`

See `docs/DBMIGRATE.md` for detailed migration instructions.

---

## Documentation Reference

### Complete Documentation
- `docs/VERIFICATION_TOOLS.md` - Verification scripts guide
- `docs/UPDATEGAMES_DECODER_001.md` - Blob format troubleshooting
- `docs/PYTHON_COMPATIBILITY_GUIDE.md` - Python integration
- `docs/BLOB_COMPATIBILITY_SOLUTION.md` - Compatibility solution
- `docs/VERIFY_RESULT_FEATURE.md` - Result verification
- `docs/NEWER_THAN_FEATURE.md` - Incremental verification
- `docs/SCHEMACHANGES.md` - Database schema changes log
- `docs/DBMIGRATE.md` - Migration commands

### Testing Documentation
- `tests/README_BLOB_TESTS.md` - Test suite documentation

---

## Adding New Programs

When creating new scripts:

1. **Make executable**: `chmod +x script.js`
2. **Add shebang**: `#!/usr/bin/env node` (for Node.js)
3. **Add --help option**: Provide usage information
4. **Document here**: Add to this file
5. **Add to package.json**: Create npm script if appropriate
6. **Write tests**: Add test cases in `tests/` directory

---

*Last Updated: October 12, 2025*  
*Total Programs: 15+ interactive scripts*

