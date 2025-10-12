#!/usr/bin/env python3
"""
verify-all-blobs.py - Comprehensive Blob Verification (Python)

Verifies all patchblobs can be decoded and are valid.

Usage:
    python3 verify-all-blobs.py [options]

Options:
    --dbtype=<type>        Database type: 'sqlite' or 'rhmd' (default: sqlite)
    --gameid=<id>          Verify specific game ID only
    --file-name=<name>     Verify specific blob file only
    --full-check           Test patches with flips (slow, comprehensive)
    --log-file=<path>      Log results to file (default: verification_results_py.log)
    --failed-file=<path>   Save failed items list (default: failed_blobs_py.json)

Exit codes:
    0 - All blobs valid
    1 - Some blobs failed verification
    2 - Fatal error
"""

import sys
import os
import json
import hashlib
import sqlite3
import subprocess
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    import blob_crypto
except ImportError:
    print("Error: blob_crypto.py not found")
    sys.exit(2)

CONFIG = {
    'DB_PATH': 'electron/rhdata.db',
    'BLOBS_DIR': 'blobs',
    'TEMP_DIR': 'temp',
    'LOG_FILE': 'verification_results_py.log',
    'FAILED_FILE': 'failed_blobs_py.json',
    'DBTYPE': 'sqlite',
    'GAMEID': None,
    'FILE_NAME': None,
    'FULL_CHECK': False,
    'FLIPS_PATH': None,
    'BASE_ROM_PATH': None
}

class VerificationLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.log_stream = open(log_file, 'w') if log_file else None
    
    def log(self, message):
        print(message)
        if self.log_stream:
            self.log_stream.write(message + '\n')
            self.log_stream.flush()
    
    def close(self):
        if self.log_stream:
            self.log_stream.close()

def verify_blob(patchblob, logger, full_check=False):
    """Verify a single patchblob"""
    gameid = patchblob.get('gameid', 'N/A')
    blob_name = patchblob['patchblob1_name']
    blob_path = os.path.join(CONFIG['BLOBS_DIR'], blob_name)
    
    result = {
        'gameid': gameid,
        'pbuuid': patchblob.get('pbuuid'),
        'patchblob1_name': blob_name,
        'file_exists': False,
        'file_hash_valid': False,
        'decode_success': False,
        'patch_hash_valid': False,
        'flips_test_success': False,
        'errors': []
    }
    
    try:
        # Check 1: Blob file exists
        if not os.path.exists(blob_path):
            result['errors'].append('Blob file not found')
            return result
        result['file_exists'] = True
        
        # Check 2: File hash matches
        with open(blob_path, 'rb') as f:
            file_data = f.read()
        
        file_hash = hashlib.sha224(file_data).hexdigest()
        
        if file_hash != patchblob['patchblob1_sha224']:
            result['errors'].append(f"File hash mismatch: expected {patchblob['patchblob1_sha224']}, got {file_hash}")
            return result
        result['file_hash_valid'] = True
        
        # Check 3: Blob can be decoded
        try:
            decoded_data = blob_crypto.decrypt_blob(
                file_data,
                patchblob['patchblob1_key'],
                patchblob['patchblob1_sha224'],
                patchblob.get('pat_sha224'),
                detect_format=True
            )
            result['decode_success'] = True
        except Exception as e:
            result['errors'].append(f"Decode failed: {e}")
            return result
        
        # Check 4: Decoded hash matches
        decoded_hash = hashlib.sha224(decoded_data).hexdigest()
        
        if decoded_hash != patchblob['pat_sha224']:
            result['errors'].append(f"Patch hash mismatch: expected {patchblob['pat_sha224']}, got {decoded_hash}")
            return result
        result['patch_hash_valid'] = True
        
        # Check 5: Full check with flips (optional)
        if full_check and CONFIG['FLIPS_PATH'] and CONFIG['BASE_ROM_PATH']:
            try:
                temp_patch = os.path.join(CONFIG['TEMP_DIR'], f"verify_{blob_name}.patch")
                temp_rom = os.path.join(CONFIG['TEMP_DIR'], f"verify_{blob_name}.sfc")
                
                with open(temp_patch, 'wb') as f:
                    f.write(decoded_data)
                
                flips_cmd = [CONFIG['FLIPS_PATH'], '--apply', temp_patch, CONFIG['BASE_ROM_PATH'], temp_rom]
                subprocess.run(flips_cmd, check=True, capture_output=True)
                
                # Clean up
                if os.path.exists(temp_patch):
                    os.remove(temp_patch)
                if os.path.exists(temp_rom):
                    os.remove(temp_rom)
                
                result['flips_test_success'] = True
            except subprocess.CalledProcessError as e:
                result['errors'].append(f"Flips test failed: exit code {e.returncode}")
            except Exception as e:
                result['errors'].append(f"Flips test failed: {e}")
        
    except Exception as e:
        result['errors'].append(f"Unexpected error: {e}")
    
    return result

def get_patchblobs_from_sqlite(gameid=None, file_name=None):
    """Get patchblobs from SQLite database"""
    conn = sqlite3.connect(CONFIG['DB_PATH'])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT pb.*, gv.gameid
        FROM patchblobs pb
        LEFT JOIN gameversions gv ON gv.gvuuid = pb.gvuuid
        WHERE pb.patchblob1_key IS NOT NULL
    """
    
    params = []
    
    if gameid:
        query += " AND gv.gameid = ?"
        params.append(gameid)
    
    if file_name:
        query += " AND pb.patchblob1_name = ?"
        params.append(file_name)
    
    query += " ORDER BY gv.gameid"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    patchblobs = [dict(row) for row in rows]
    
    conn.close()
    return patchblobs

def get_patchblobs_from_rhmd(gameid=None, file_name=None):
    """Get patchblobs from RHMD file"""
    try:
        import loadsmwrh
        
        hacklist = loadsmwrh.get_hacklist_data()
        patchblobs = []
        
        for hack in hacklist:
            # Filter by gameid if specified
            if gameid and str(hack.get('id')) != str(gameid):
                continue
            
            # Get patchblob info from hack
            if 'xdata' in hack and hack['xdata']:
                blob_name = hack['xdata'].get('patchblob1_name')
                blob_key = hack['xdata'].get('patchblob1_key')
                blob_sha224 = hack['xdata'].get('patchblob1_sha224')
            else:
                blob_name = hack.get('patchblob1_name')
                blob_key = hack.get('patchblob1_key')
                blob_sha224 = hack.get('patchblob1_sha224')
            
            if not (blob_name and blob_key and blob_sha224):
                continue
            
            # Filter by file name if specified
            if file_name and blob_name != file_name:
                continue
            
            patchblob = {
                'gameid': hack.get('id'),
                'pbuuid': None,
                'patchblob1_name': blob_name,
                'patchblob1_key': blob_key,
                'patchblob1_sha224': blob_sha224,
                'pat_sha224': hack.get('pat_sha224'),
                'source': 'rhmd'
            }
            
            patchblobs.append(patchblob)
        
        return patchblobs
        
    except Exception as e:
        print(f"Error loading RHMD file: {e}")
        return []

def main():
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Verify all patchblobs')
    parser.add_argument('--dbtype', choices=['sqlite', 'rhmd'], default='sqlite', help='Database type')
    parser.add_argument('--gameid', help='Verify specific game ID only')
    parser.add_argument('--file-name', help='Verify specific blob file only')
    parser.add_argument('--full-check', action='store_true', help='Test with flips (slow)')
    parser.add_argument('--log-file', default='verification_results_py.log', help='Log file path')
    parser.add_argument('--failed-file', default='failed_blobs_py.json', help='Failed items file')
    
    args = parser.parse_args()
    
    CONFIG['DBTYPE'] = args.dbtype
    CONFIG['GAMEID'] = args.gameid
    CONFIG['FILE_NAME'] = args.file_name
    CONFIG['FULL_CHECK'] = args.full_check
    CONFIG['LOG_FILE'] = args.log_file
    CONFIG['FAILED_FILE'] = args.failed_file
    
    print('=' * 70)
    print('BLOB VERIFICATION UTILITY (Python)')
    print('=' * 70)
    print(f"Database type: {CONFIG['DBTYPE']}")
    
    if CONFIG['FULL_CHECK']:
        print('⚠️  FULL CHECK MODE - Will test patches with flips (SLOW)\n')
        
        # Find flips and base ROM
        try:
            # Try to find flips
            for flips_path in ['/usr/local/bin/flips', './flips', 'flips']:
                if os.path.exists(flips_path) or subprocess.run(['which', 'flips'], capture_output=True).returncode == 0:
                    CONFIG['FLIPS_PATH'] = flips_path
                    break
            
            # Find base ROM
            if os.path.exists('smw.sfc'):
                CONFIG['BASE_ROM_PATH'] = 'smw.sfc'
            
            if CONFIG['FLIPS_PATH'] and CONFIG['BASE_ROM_PATH']:
                print(f"✓ Flips: {CONFIG['FLIPS_PATH']}")
                print(f"✓ Base ROM: {CONFIG['BASE_ROM_PATH']}\n")
            else:
                print('✗ Cannot run full check: flips or smw.sfc not found')
                print('Continuing without flips verification...\n')
                CONFIG['FULL_CHECK'] = False
                
        except Exception as e:
            print(f'✗ Cannot run full check: {e}')
            CONFIG['FULL_CHECK'] = False
    
    if CONFIG['LOG_FILE']:
        print(f"📝 Logging to: {CONFIG['LOG_FILE']}\n")
    
    logger = VerificationLogger(CONFIG['LOG_FILE'])
    
    try:
        # Get patchblobs from appropriate source
        if CONFIG['DBTYPE'] == 'sqlite':
            patchblobs = get_patchblobs_from_sqlite(CONFIG['GAMEID'], CONFIG['FILE_NAME'])
        else:  # rhmd
            patchblobs = get_patchblobs_from_rhmd(CONFIG['GAMEID'], CONFIG['FILE_NAME'])
        
        logger.log(f"\nFound {len(patchblobs)} patchblobs to verify\n")
        logger.log('=' * 70)
        
        verified = 0
        failed = 0
        failures = []
        
        for i, pb in enumerate(patchblobs):
            progress = f"[{i + 1}/{len(patchblobs)}]"
            logger.log(f"\n{progress} Game {pb.get('gameid', 'N/A')}: {pb['patchblob1_name']}")
            
            result = verify_blob(pb, logger, CONFIG['FULL_CHECK'])
            
            if not result['errors'] and result['patch_hash_valid']:
                flips_msg = ' (flips test passed)' if CONFIG['FULL_CHECK'] and result['flips_test_success'] else ''
                logger.log(f"  ✅ VALID{flips_msg}")
                verified += 1
            else:
                logger.log(f"  ❌ FAILED:")
                for err in result['errors']:
                    logger.log(f"     - {err}")
                failed += 1
                failures.append(result)
        
        logger.log('\n' + '=' * 70)
        logger.log('VERIFICATION SUMMARY')
        logger.log('=' * 70)
        logger.log(f"Total blobs:    {len(patchblobs)}")
        logger.log(f"✅ Valid:        {verified}")
        logger.log(f"❌ Failed:       {failed}")
        logger.log('=' * 70)
        
        # Save failures
        if failures:
            failed_data = {
                'timestamp': datetime.now().isoformat(),
                'dbtype': CONFIG['DBTYPE'],
                'total_checked': len(patchblobs),
                'failed_count': failed,
                'failures': failures
            }
            
            with open(CONFIG['FAILED_FILE'], 'w') as f:
                json.dump(failed_data, f, indent=2)
            
            logger.log(f"\n❌ Failed blobs saved to: {CONFIG['FAILED_FILE']}")
        
        logger.close()
        sys.exit(1 if failed > 0 else 0)
        
    except Exception as e:
        logger.log(f"\n❌ Fatal error: {e}")
        import traceback
        logger.log(traceback.format_exc())
        logger.close()
        sys.exit(2)

if __name__ == '__main__':
    main()

