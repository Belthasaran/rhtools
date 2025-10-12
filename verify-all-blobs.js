#!/usr/bin/env node
/**
 * verify-all-blobs.js - Comprehensive Blob Verification
 * 
 * Verifies all patchblobs in the SQLite database can be decoded and are valid.
 * 
 * Usage:
 *   node verify-all-blobs.js [options]
 * 
 * Options:
 *   --gameid=<id>          Verify specific game ID only
 *   --file-name=<name>     Verify specific blob file only
 *   --full-check           Test patches with flips (slow, comprehensive)
 *   --log-file=<path>      Log results to file (default: verification_results.log)
 *   --failed-file=<path>   Save failed items list (default: failed_blobs.json)
 * 
 * Exit codes:
 *   0 - All blobs valid
 *   1 - Some blobs failed verification
 *   2 - Fatal error
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');
const DatabaseManager = require('./lib/database');
const RecordCreator = require('./lib/record-creator');
const { getFlipsPath, getSmwRomPath } = require('./lib/binary-finder');

const CONFIG = {
  DB_PATH: path.join(__dirname, 'electron', 'rhdata.db'),
  PATCHBIN_DB_PATH: path.join(__dirname, 'electron', 'patchbin.db'),
  BLOBS_DIR: path.join(__dirname, 'blobs'),
  TEMP_DIR: path.join(__dirname, 'temp'),
  LOG_FILE: 'verification_results.log',
  FAILED_FILE: 'failed_blobs.json',
  FULL_CHECK: false,
  GAMEID: null,
  FILE_NAME: null,
  FLIPS_PATH: null,
  BASE_ROM_PATH: null
};

function parseArgs(args) {
  const parsed = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg.startsWith('--gameid=')) {
      parsed.gameid = arg.split('=')[1];
    } else if (arg === '--gameid') {
      parsed.gameid = args[++i];
    } else if (arg.startsWith('--file-name=')) {
      parsed.fileName = arg.split('=')[1];
    } else if (arg === '--file-name') {
      parsed.fileName = args[++i];
    } else if (arg === '--full-check') {
      parsed.fullCheck = true;
    } else if (arg.startsWith('--log-file=')) {
      parsed.logFile = arg.split('=')[1];
    } else if (arg === '--log-file') {
      parsed.logFile = args[++i];
    } else if (arg.startsWith('--failed-file=')) {
      parsed.failedFile = arg.split('=')[1];
    } else if (arg === '--failed-file') {
      parsed.failedFile = args[++i];
    }
  }
  
  return parsed;
}

class VerificationLogger {
  constructor(logFile) {
    this.logFile = logFile;
    this.logStream = logFile ? fs.createWriteStream(logFile, { flags: 'w' }) : null;
  }
  
  log(message) {
    console.log(message);
    if (this.logStream) {
      this.logStream.write(message + '\n');
    }
  }
  
  close() {
    if (this.logStream) {
      this.logStream.end();
    }
  }
}

async function verifyBlob(patchblob, recordCreator, logger, fullCheck = false) {
  const gameid = patchblob.gameid || 'N/A';
  const blobName = patchblob.patchblob1_name;
  const blobPath = path.join(CONFIG.BLOBS_DIR, blobName);
  
  const result = {
    gameid,
    pbuuid: patchblob.pbuuid,
    patchblob1_name: blobName,
    file_exists: false,
    file_hash_valid: false,
    decode_success: false,
    patch_hash_valid: false,
    flips_test_success: false,
    errors: []
  };
  
  try {
    // Check 1: Blob file exists
    if (!fs.existsSync(blobPath)) {
      result.errors.push('Blob file not found');
      return result;
    }
    result.file_exists = true;
    
    // Check 2: File hash matches
    const fileData = fs.readFileSync(blobPath);
    const fileHash = crypto.createHash('sha224').update(fileData).digest('hex');
    
    if (fileHash !== patchblob.patchblob1_sha224) {
      result.errors.push(`File hash mismatch: expected ${patchblob.patchblob1_sha224}, got ${fileHash}`);
      return result;
    }
    result.file_hash_valid = true;
    
    // Check 3: Blob can be decoded
    let decodedData;
    try {
      decodedData = await recordCreator.decodeBlob(fileData, patchblob.patchblob1_key);
      result.decode_success = true;
    } catch (error) {
      result.errors.push(`Decode failed: ${error.message}`);
      return result;
    }
    
    // Check 4: Decoded hash matches
    const decodedHash = crypto.createHash('sha224').update(decodedData).digest('hex');
    
    if (decodedHash !== patchblob.pat_sha224) {
      result.errors.push(`Patch hash mismatch: expected ${patchblob.pat_sha224}, got ${decodedHash}`);
      return result;
    }
    result.patch_hash_valid = true;
    
    // Check 5: Full check with flips (optional)
    if (fullCheck && CONFIG.FLIPS_PATH && CONFIG.BASE_ROM_PATH) {
      try {
        const tempPatch = path.join(CONFIG.TEMP_DIR, `verify_${blobName}.patch`);
        const tempRom = path.join(CONFIG.TEMP_DIR, `verify_${blobName}.sfc`);
        
        fs.writeFileSync(tempPatch, decodedData);
        
        const flipsCmd = `"${CONFIG.FLIPS_PATH}" --apply "${tempPatch}" "${CONFIG.BASE_ROM_PATH}" "${tempRom}"`;
        execSync(flipsCmd, { stdio: 'pipe' });
        
        // Clean up
        fs.unlinkSync(tempPatch);
        if (fs.existsSync(tempRom)) {
          fs.unlinkSync(tempRom);
        }
        
        result.flips_test_success = true;
      } catch (error) {
        result.errors.push(`Flips test failed: ${error.message}`);
      }
    }
    
  } catch (error) {
    result.errors.push(`Unexpected error: ${error.message}`);
  }
  
  return result;
}

async function main() {
  const argv = parseArgs(process.argv.slice(2));
  
  CONFIG.GAMEID = argv.gameid || null;
  CONFIG.FILE_NAME = argv.fileName || null;
  CONFIG.FULL_CHECK = argv.fullCheck || false;
  CONFIG.LOG_FILE = argv.logFile || CONFIG.LOG_FILE;
  CONFIG.FAILED_FILE = argv.failedFile || CONFIG.FAILED_FILE;
  
  console.log('='.repeat(70));
  console.log('BLOB VERIFICATION UTILITY');
  console.log('='.repeat(70));
  
  if (CONFIG.FULL_CHECK) {
    console.log('⚠️  FULL CHECK MODE - Will test patches with flips (SLOW)\n');
    
    try {
      CONFIG.FLIPS_PATH = getFlipsPath({ projectRoot: __dirname });
      CONFIG.BASE_ROM_PATH = getSmwRomPath({ projectRoot: __dirname, throwOnError: true });
      console.log(`✓ Flips: ${CONFIG.FLIPS_PATH}`);
      console.log(`✓ Base ROM: ${CONFIG.BASE_ROM_PATH}\n`);
    } catch (error) {
      console.error('✗ Cannot run full check:', error.message);
      console.log('Continuing without flips verification...\n');
      CONFIG.FULL_CHECK = false;
    }
  }
  
  if (CONFIG.LOG_FILE) {
    console.log(`📝 Logging to: ${CONFIG.LOG_FILE}\n`);
  }
  
  const logger = new VerificationLogger(CONFIG.LOG_FILE);
  
  try {
    const dbManager = new DatabaseManager(CONFIG.DB_PATH);
    const recordCreator = new RecordCreator(dbManager, CONFIG.PATCHBIN_DB_PATH, CONFIG);
    
    // Build query
    let query = `
      SELECT pb.*, gv.gameid
      FROM patchblobs pb
      LEFT JOIN gameversions gv ON gv.gvuuid = pb.gvuuid
      WHERE pb.patchblob1_key IS NOT NULL
    `;
    
    const params = [];
    
    if (CONFIG.GAMEID) {
      query += ` AND gv.gameid = ?`;
      params.push(CONFIG.GAMEID);
      logger.log(`Filtering to game ID: ${CONFIG.GAMEID}`);
    }
    
    if (CONFIG.FILE_NAME) {
      query += ` AND pb.patchblob1_name = ?`;
      params.push(CONFIG.FILE_NAME);
      logger.log(`Filtering to file: ${CONFIG.FILE_NAME}`);
    }
    
    query += ` ORDER BY gv.gameid`;
    
    const patchblobs = dbManager.db.prepare(query).all(...params);
    
    logger.log(`\nFound ${patchblobs.length} patchblobs to verify\n`);
    logger.log('='.repeat(70));
    
    let verified = 0;
    let failed = 0;
    const failures = [];
    
    for (let i = 0; i < patchblobs.length; i++) {
      const pb = patchblobs[i];
      const progress = `[${i + 1}/${patchblobs.length}]`;
      
      logger.log(`\n${progress} Game ${pb.gameid || 'N/A'}: ${pb.patchblob1_name}`);
      
      const result = await verifyBlob(pb, recordCreator, logger, CONFIG.FULL_CHECK);
      
      if (result.errors.length === 0 && result.patch_hash_valid) {
        logger.log(`  ✅ VALID${CONFIG.FULL_CHECK && result.flips_test_success ? ' (flips test passed)' : ''}`);
        verified++;
      } else {
        logger.log(`  ❌ FAILED:`);
        result.errors.forEach(err => logger.log(`     - ${err}`));
        failed++;
        failures.push(result);
      }
    }
    
    logger.log('\n' + '='.repeat(70));
    logger.log('VERIFICATION SUMMARY');
    logger.log('='.repeat(70));
    logger.log(`Total blobs:    ${patchblobs.length}`);
    logger.log(`✅ Valid:        ${verified}`);
    logger.log(`❌ Failed:       ${failed}`);
    logger.log('='.repeat(70));
    
    // Save failures to file
    if (failures.length > 0) {
      const failedData = {
        timestamp: new Date().toISOString(),
        total_checked: patchblobs.length,
        failed_count: failed,
        failures: failures.map(f => ({
          gameid: f.gameid,
          pbuuid: f.pbuuid,
          patchblob1_name: f.patchblob1_name,
          errors: f.errors,
          checks: {
            file_exists: f.file_exists,
            file_hash_valid: f.file_hash_valid,
            decode_success: f.decode_success,
            patch_hash_valid: f.patch_hash_valid,
            flips_test_success: f.flips_test_success
          }
        }))
      };
      
      fs.writeFileSync(CONFIG.FAILED_FILE, JSON.stringify(failedData, null, 2));
      logger.log(`\n❌ Failed blobs saved to: ${CONFIG.FAILED_FILE}`);
    }
    
    recordCreator.close();
    dbManager.close();
    logger.close();
    
    process.exit(failed > 0 ? 1 : 0);
    
  } catch (error) {
    logger.log(`\n❌ Fatal error: ${error.message}`);
    logger.log(error.stack);
    logger.close();
    process.exit(2);
  }
}

if (require.main === module) {
  main();
}

module.exports = { verifyBlob };

