# Blob Verification Tools Documentation

**Date**: October 12, 2025  
**Tools**: verify-all-blobs.js, verify-all-blobs.py

---

## Overview

Comprehensive verification utilities to ensure blob integrity across the entire database.

Both JavaScript and Python versions provide identical functionality with two verification modes:
- **files**: Verify blob files from `blobs/` directory
- **db**: Verify blob data from `patchbin.db` file_data column

---

## Quick Start

### Verify All Blobs (from files)
```bash
npm run verify:blobs
# or
node verify-all-blobs.js --verify-blobs=files
```

### Verify All Blobs (from database)
```bash
npm run verify:blobs-db
# or
node verify-all-blobs.js --verify-blobs=db
```

### Full Check (with flips)
```bash
npm run verify:blobs-full         # From files
npm run verify:blobs-db-full      # From database
```

---

## verify-all-blobs.js (JavaScript)

### Usage

```bash
node verify-all-blobs.js [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--verify-blobs=<source>` | Blob source: 'db' or 'files' | files |
| `--gameid=<id>` | Verify specific game ID only | all |
| `--file-name=<name>` | Verify specific blob file only | all |
| `--full-check` | Test patches with flips (slow) | false |
| `--log-file=<path>` | Log results to file | verification_results.log |
| `--failed-file=<path>` | Save failed items list | failed_blobs.json |

### Verification Levels

#### Basic Verification (default)
- ✓ Blob file/data exists
- ✓ file_hash_sha224 matches blob data
- ✓ Blob can be decoded
- ✓ pat_sha224 matches decoded patch

#### Full Verification (--full-check)
- ✓ All basic checks
- ✓ Patch applies successfully with flips
- ✓ Flips exits with success code

### Examples

```bash
# Verify all blobs from files
node verify-all-blobs.js --verify-blobs=files

# Verify all blobs from database
node verify-all-blobs.js --verify-blobs=db

# Verify specific game (from files)
node verify-all-blobs.js --verify-blobs=files --gameid=40663

# Verify specific blob (from database)
node verify-all-blobs.js --verify-blobs=db --file-name=pblob_40663_60a76bf9c7

# Full check with flips (from files)
node verify-all-blobs.js --verify-blobs=files --full-check --log-file=full_verify.log

# Full check specific game (from database)
node verify-all-blobs.js --verify-blobs=db --gameid=40663 --full-check
```

### Output Format

```
======================================================================
BLOB VERIFICATION UTILITY
======================================================================
Verification source: blob files

Found 3120 patchblobs to verify

======================================================================

[1/3120] Game 4982: pblob_4982_d61803aa91
  ✅ VALID

[2/3120] Game 5987: pblob_5987_ae43644a54
  ✅ VALID

...

======================================================================
VERIFICATION SUMMARY
======================================================================
Total blobs:    3120
✅ Valid:        3115
❌ Failed:       5
======================================================================

❌ Failed blobs saved to: failed_blobs.json
```

### Failed Blobs JSON Format

```json
{
  "timestamp": "2025-10-12T10:30:00.000Z",
  "total_checked": 3120,
  "failed_count": 5,
  "failures": [
    {
      "gameid": "12345",
      "pbuuid": "abc-def-...",
      "patchblob1_name": "pblob_12345_abcdef1234",
      "errors": ["Blob file not found"],
      "checks": {
        "file_exists": false,
        "file_hash_valid": false,
        "decode_success": false,
        "patch_hash_valid": false,
        "flips_test_success": false
      }
    }
  ]
}
```

---

## verify-all-blobs.py (Python)

### Usage

```bash
python3 verify-all-blobs.py [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dbtype=<type>` | Database type: 'sqlite' or 'rhmd' | sqlite |
| `--verify-blobs=<source>` | Blob source: 'db' or 'files' | files |
| `--gameid=<id>` | Verify specific game ID only | all |
| `--file-name=<name>` | Verify specific blob file only | all |
| `--full-check` | Test patches with flips (slow) | false |
| `--log-file=<path>` | Log results to file | verification_results_py.log |
| `--failed-file=<path>` | Save failed items list | failed_blobs_py.json |

### Examples

```bash
# Verify SQLite database blobs (from files)
python3 verify-all-blobs.py --dbtype=sqlite --verify-blobs=files

# Verify SQLite database blobs (from patchbin.db)
python3 verify-all-blobs.py --dbtype=sqlite --verify-blobs=db

# Verify RHMD file blobs
python3 verify-all-blobs.py --dbtype=rhmd --verify-blobs=files

# Verify specific game (from database)
python3 verify-all-blobs.py --dbtype=sqlite --verify-blobs=db --gameid=40663

# Full check with flips
python3 verify-all-blobs.py --dbtype=sqlite --full-check --log-file=py_verify.log

# Verify specific blob from RHMD file
python3 verify-all-blobs.py --dbtype=rhmd --file-name=pblob_4982_d61803aa91
```

---

## Verification Sources Explained

### --verify-blobs=files (Default)

**What it checks**:
- Reads blob files from `blobs/` directory
- Verifies file_hash_sha224 against actual file
- Ensures files haven't been corrupted or modified

**Use when**:
- ✅ Verifying filesystem blob integrity
- ✅ Detecting missing or corrupted files
- ✅ Standard verification workflow

**Performance**: Fast (direct file I/O)

### --verify-blobs=db

**What it checks**:
- Reads blob data from `patchbin.db` attachments.file_data column
- Verifies file_hash_sha224 against stored data
- Ensures database integrity

**Use when**:
- ✅ Verifying database blob integrity
- ✅ Testing without filesystem access
- ✅ Checking for database corruption
- ✅ Verifying attachments can be decoded

**Performance**: Slower (SQLite BLOB retrieval)

**Important**: If verification passes with `--verify-blobs=db` but fails with `--verify-blobs=files`, the blob files are corrupted or missing. Recreate them from the database.

---

## Full Check Mode (--full-check)

### What It Does

In addition to basic verification, full check mode:

1. **Saves decoded patch** to temporary file
2. **Runs flips** to apply patch to SMW ROM
3. **Verifies flips** exits successfully
4. **Cleans up** temporary files

### Requirements

- `flips` executable must be available
- `smw.sfc` base ROM must be present

### Example Output

```
[1/10] Game 40663: pblob_40663_60a76bf9c7
  ✅ VALID (flips test passed)
```

### When to Use

- Before production deployment
- After database migration
- When suspicious patch issues occur
- Monthly/quarterly integrity audits

### Performance Impact

**Without full check**: ~50-100 blobs/second  
**With full check**: ~2-5 blobs/second

**Recommendation**: Use `--gameid` or `--file-name` with full check for testing, run full database verification overnight.

---

## Common Use Cases

### Daily Health Check
```bash
# Quick verify (from files)
npm run verify:blobs

# Expected: All blobs valid ✅
```

### After Database Migration
```bash
# Verify database integrity
npm run verify:blobs-db

# Then verify files match database
npm run verify:blobs
```

### Investigate Specific Issue
```bash
# Verify one game's blobs
node verify-all-blobs.js --gameid=40663 --full-check

# Verify one specific blob
node verify-all-blobs.js --file-name=pblob_40663_60a76bf9c7 --full-check
```

### Comprehensive Audit
```bash
# Full database verification with logging
node verify-all-blobs.js --verify-blobs=db --full-check \
  --log-file=audit_$(date +%Y%m%d).log \
  --failed-file=failed_$(date +%Y%m%d).json

# Review failures
cat failed_$(date +%Y%m%d).json | jq '.failures[].errors'
```

### RHMD File Verification
```bash
# Verify RHMD file blobs (Python only)
python3 verify-all-blobs.py --dbtype=rhmd --verify-blobs=files

# With full check
python3 verify-all-blobs.py --dbtype=rhmd --full-check
```

---

## Interpreting Results

### All Valid
```
✅ Valid:        3120
❌ Failed:       0
```
**Action**: None needed - database is healthy

### Missing Files
```
❌ Failed:       5
Errors: "Blob file not found on filesystem"
```
**Action**: Recreate blobs from database or reprocess games

### Hash Mismatches
```
❌ Failed:       2
Errors: "File hash mismatch"
```
**Action**: Files corrupted - restore from backup or recreate

### Decode Failures
```
❌ Failed:       1
Errors: "Decode failed: File format not recognized"
```
**Action**: Incompatible format - check with identify-incompatible-keys.js

### Flips Test Failures
```
❌ Failed:       3
Errors: "Flips test failed: exit code 1"
```
**Action**: Invalid patch data - may need redownload

---

## Performance Guidelines

### Small Datasets (< 100 blobs)
```bash
# Can use full check
node verify-all-blobs.js --full-check
```

### Medium Datasets (100-1000 blobs)
```bash
# Sample check with full verification
node verify-all-blobs.js --gameid=<sample_id> --full-check

# Basic check for all
node verify-all-blobs.js
```

### Large Datasets (> 1000 blobs)
```bash
# Basic check only (fast)
npm run verify:blobs

# Full check in background overnight
nohup node verify-all-blobs.js --full-check --log-file=full_verify.log &
```

---

## Integration with CI/CD

### Pre-Deployment Check

```bash
#!/bin/bash
# pre-deploy.sh

echo "Running blob verification..."
node verify-all-blobs.js --verify-blobs=db --log-file=pre-deploy.log

if [ $? -eq 0 ]; then
  echo "✅ All blobs valid - proceeding with deployment"
  exit 0
else
  echo "❌ Blob verification failed - aborting deployment"
  cat failed_blobs.json
  exit 1
fi
```

### Nightly Audit

```bash
#!/bin/bash
# nightly-audit.sh

DATE=$(date +%Y%m%d)

# Verify from database
node verify-all-blobs.js --verify-blobs=db \
  --log-file=audit_db_$DATE.log \
  --failed-file=failed_db_$DATE.json

# Verify from files
node verify-all-blobs.js --verify-blobs=files \
  --log-file=audit_files_$DATE.log \
  --failed-file=failed_files_$DATE.json

# Compare results
# If db passes but files fail → File corruption
# If files pass but db fails → Database corruption
```

---

## Troubleshooting

### "Blob file not found"

```bash
# Check if blob exists
ls -lh blobs/pblob_XXXXX

# If missing, check database
sqlite3 electron/patchbin.db "SELECT length(file_data) FROM attachments WHERE file_name='pblob_XXXXX'"

# Recreate if database has it
node reprocess-attachments.js --game-ids=XXXXX
```

### "File hash mismatch"

```bash
# File corrupted - verify against database
node verify-all-blobs.js --verify-blobs=db --file-name=pblob_XXXXX

# If db version valid, restore from database
sqlite3 electron/patchbin.db "SELECT writefile('blobs/pblob_XXXXX', file_data) FROM attachments WHERE file_name='pblob_XXXXX'"
```

### "Decode failed"

```bash
# Check key format
node identify-incompatible-keys.js

# If incompatible, reprocess
node updategames.js --game-ids=XXXXX
```

### "Flips test failed"

```bash
# Test manually
python3 blob_crypto.py decrypt blobs/pblob_XXXXX <key> <hash> temp/test.patch
flips --apply temp/test.patch smw.sfc temp/result.sfc

# If flips fails, patch may be invalid - redownload game
```

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | All blobs valid | ✅ No action needed |
| 1 | Some blobs failed | Review failed_blobs.json |
| 2 | Fatal error | Check error message |

---

## Performance Benchmarks

Hardware: Standard server  
Dataset: 3,120 blobs

| Mode | Time | Rate |
|------|------|------|
| files (basic) | ~30 seconds | ~100 blobs/sec |
| db (basic) | ~60 seconds | ~50 blobs/sec |
| files (full-check) | ~45 minutes | ~1.2 blobs/sec |
| db (full-check) | ~50 minutes | ~1.0 blobs/sec |

**Recommendation**: Use basic verification for routine checks, full-check for audits.

---

## Automated Monitoring

### Cron Job Example

```cron
# Daily basic verification
0 2 * * * cd /path/to/rhtools && npm run verify:blobs > /tmp/verify.log 2>&1

# Weekly full check (Sunday 2 AM)
0 2 * * 0 cd /path/to/rhtools && npm run verify:blobs-full > /tmp/verify_full.log 2>&1
```

### Alert on Failure

```bash
#!/bin/bash
npm run verify:blobs

if [ $? -ne 0 ]; then
  # Send alert
  mail -s "Blob verification failed" admin@example.com < failed_blobs.json
fi
```

---

## See Also

- `docs/UPDATEGAMES_DECODER_001.md` - Blob format documentation
- `docs/PYTHON_COMPATIBILITY_GUIDE.md` - Python integration
- `docs/BLOB_COMPATIBILITY_SOLUTION.md` - Complete solution guide
- `tests/README_BLOB_TESTS.md` - Test suite documentation

