#!/usr/bin/env node

/**
 * fetchpatches.js - Fetch and manage patch attachments from ArDrive and other sources
 * 
 * Usage:
 *   node fetchpatches.js mode1          # Populate ArDrive metadata for attachments
 *   node fetchpatches.js mode2          # Find and download missing attachment data
 *   node fetchpatches.js mode3 [args]   # Retrieve specific attachment
 * 
 * Mode 1: Scan attachments table for missing ArDrive metadata and populate it
 * Mode 2: Find and download missing file_data (future implementation)
 * Mode 3: Retrieve specific attachment (future implementation)
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const Database = require('better-sqlite3');
const arDriveCore = require('ardrive-core-js');
const arweave = require('arweave');

// Database paths
const RHDATA_DB_PATH = path.join(__dirname, 'electron', 'rhdata.db');
const PATCHBIN_DB_PATH = path.join(__dirname, 'electron', 'patchbin.db');

// ArDrive configuration
const DEFAULT_GATEWAY = 'https://arweave.net:443';
const PUBLIC_FOLDER_ID = '07b13d74-e426-4012-8c6d-cba0927012fb';

// Default parameters for remote fetching
const DEFAULT_FETCH_LIMIT = 20;
const DEFAULT_FETCH_DELAY = 1000; // milliseconds
const MIN_FETCH_DELAY = 500; // minimum 500ms to avoid server overload

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Parse command line arguments for fetch parameters
 */
function parseArguments(args) {
  const params = {
    mode: null,
    fetchLimit: DEFAULT_FETCH_LIMIT,
    fetchDelay: DEFAULT_FETCH_DELAY,
    extraArgs: []
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg.startsWith('--fetchlimit=')) {
      const value = parseInt(arg.split('=')[1], 10);
      if (isNaN(value) || value < 1) {
        console.error(`Invalid fetchlimit value: ${arg.split('=')[1]}`);
        console.error('fetchlimit must be a positive integer');
        process.exit(1);
      }
      params.fetchLimit = value;
    } else if (arg.startsWith('--fetchdelay=')) {
      const value = parseInt(arg.split('=')[1], 10);
      if (isNaN(value) || value < MIN_FETCH_DELAY) {
        console.error(`Invalid fetchdelay value: ${arg.split('=')[1]}`);
        console.error(`fetchdelay must be at least ${MIN_FETCH_DELAY}ms`);
        process.exit(1);
      }
      params.fetchDelay = value;
    } else if (i === 0) {
      params.mode = arg.toLowerCase();
    } else {
      params.extraArgs.push(arg);
    }
  }
  
  return params;
}

/**
 * Initialize ArDrive anonymous client
 */
function initArDrive() {
  const arweaveUrl = new URL(DEFAULT_GATEWAY);
  const arweaveClient = arweave.init({
    host: arweaveUrl.hostname,
    protocol: arweaveUrl.protocol.replace(':', ''),
    port: arweaveUrl.port || 443,
    timeout: 600000
  });
  
  return arDriveCore.arDriveAnonymousFactory({ arweave: arweaveClient });
}

/**
 * List all files in the public ArDrive folder
 */
async function listArDriveFiles(arDrive) {
  try {
    const folderId = arDriveCore.EID(PUBLIC_FOLDER_ID);
    const files = await arDrive.listPublicFolder({ folderId: folderId, maxDepth: 10 });
    
    console.log(`Found ${files.length} items on ArDrive`);
    
    // Filter to only files (not folders)
    const fileItems = files.filter(item => item.entityType === 'file');
    console.log(`  ${fileItems.length} files`);
    console.log(`  ${files.length - fileItems.length} folders`);
    
    return fileItems;
  } catch (error) {
    console.error('Error listing ArDrive files:', error);
    throw error;
  }
}

/**
 * Download a file from ArDrive by transaction ID
 */
async function downloadArDriveFile(txId) {
  try {
    const url = `${DEFAULT_GATEWAY}/${txId}`;
    console.log(`    Downloading from ${url}`);
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  } catch (error) {
    console.error(`    Error downloading file: ${error.message}`);
    return null;
  }
}

/**
 * Calculate SHA-224 hash
 */
function sha224(buffer) {
  return crypto.createHash('sha224').update(buffer).digest('hex');
}

/**
 * Calculate SHA-256 hash
 */
function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

/**
 * Calculate SHA-1 hash
 */
function sha1(buffer) {
  return crypto.createHash('sha1').update(buffer).digest('hex');
}

/**
 * Verify file hash against attachment record using secure hashes
 * Returns true if file matches, false otherwise
 */
function verifyFileHash(fileData, attachment) {
  // Priority: Use strongest hash available
  
  // SHA-256 (most secure and commonly used)
  if (attachment.file_hash_sha256) {
    const fileHash = sha256(fileData);
    if (fileHash === attachment.file_hash_sha256) {
      console.log(`    ✓ Verified with SHA-256: ${fileHash}`);
      return true;
    }
  }
  
  // SHA-224
  if (attachment.file_hash_sha224) {
    const fileHash = sha224(fileData);
    if (fileHash === attachment.file_hash_sha224) {
      console.log(`    ✓ Verified with SHA-224: ${fileHash}`);
      return true;
    }
  }
  
  // Decoded hashes (for encrypted files)
  if (attachment.decoded_hash_sha256) {
    const fileHash = sha256(fileData);
    if (fileHash === attachment.decoded_hash_sha256) {
      console.log(`    ✓ Verified with decoded SHA-256: ${fileHash}`);
      return true;
    }
  }
  
  if (attachment.decoded_hash_sha224) {
    const fileHash = sha224(fileData);
    if (fileHash === attachment.decoded_hash_sha224) {
      console.log(`    ✓ Verified with decoded SHA-224: ${fileHash}`);
      return true;
    }
  }
  
  console.log(`    ✗ Hash verification failed`);
  return false;
}

/**
 * Match ArDrive files with attachment records
 */
function matchFileToAttachment(ardriveFile, attachments) {
  const fileName = ardriveFile.name;
  
  // Try exact file name match first
  for (const attachment of attachments) {
    // Match exact name
    if (attachment.file_name === fileName) {
      return attachment;
    }
    
    // Match name without extension (.bin)
    if (fileName.endsWith('.bin') && attachment.file_name === fileName.slice(0, -4)) {
      return attachment;
    }
    
    // Match name with extension added
    if (attachment.file_name + '.bin' === fileName) {
      return attachment;
    }
  }
  
  return null;
}

/**
 * Mode 1: Populate ArDrive metadata for attachments with missing ArDrive info
 */
async function mode1_populateArDriveMetadata(fetchLimit = DEFAULT_FETCH_LIMIT, fetchDelay = DEFAULT_FETCH_DELAY) {
  console.log('='.repeat(70));
  console.log('MODE 1: Populate ArDrive Metadata');
  console.log('='.repeat(70));
  console.log();
  console.log(`Configuration:`);
  console.log(`  Fetch Limit: ${fetchLimit} attachments per run`);
  console.log(`  Fetch Delay: ${fetchDelay}ms between each attachment`);
  console.log();
  
  // Check if databases exist
  if (!fs.existsSync(PATCHBIN_DB_PATH)) {
    console.error(`Error: patchbin.db not found at ${PATCHBIN_DB_PATH}`);
    process.exit(1);
  }
  
  // Open database
  const db = new Database(PATCHBIN_DB_PATH);
  
  try {
    // Initialize ArDrive
    console.log('Initializing ArDrive client...');
    const arDrive = initArDrive();
    
    // List all files on ArDrive
    console.log(`\nListing files from ArDrive folder: ${PUBLIC_FOLDER_ID}`);
    const ardriveFiles = await listArDriveFiles(arDrive);
    
    // Get attachments with missing ArDrive metadata
    console.log('\nQuerying attachments with missing ArDrive metadata...');
    const query = `
      SELECT auuid, pbuuid, gvuuid, resuuid,
             file_name, file_hash_sha224, file_hash_sha256,
             file_ipfs_cidv0, file_ipfs_cidv1,
             decoded_hash_sha224, decoded_hash_sha256,
             arweave_file_name, arweave_file_id, arweave_file_path
      FROM attachments
      WHERE arweave_file_id IS NULL 
         OR arweave_file_name IS NULL 
         OR arweave_file_path IS NULL
    `;
    
    const attachments = db.prepare(query).all();
    console.log(`Found ${attachments.length} attachments with missing ArDrive metadata`);
    
    if (attachments.length === 0) {
      console.log('\n✓ All attachments already have ArDrive metadata!');
      return;
    }
    
    console.log('\n' + '='.repeat(70));
    console.log('Processing attachments...\n');
    
    let processed = 0;
    let matched = 0;
    let verified = 0;
    let updated = 0;
    let failed = 0;
    
    // Process each ArDrive file
    for (const ardriveFile of ardriveFiles) {
      // Only process files, not folders
      if (ardriveFile.entityType !== 'file') {
        continue;
      }
      
      // Try to match with an attachment
      const attachment = matchFileToAttachment(ardriveFile, attachments);
      
      if (!attachment) {
        continue;
      }
      
      // Check if we've reached the fetch limit
      if (processed >= fetchLimit) {
        console.log(`\n⚠ Reached fetch limit of ${fetchLimit} attachments`);
        console.log(`  Stopping to avoid server overload`);
        console.log(`  Run the script again to process more attachments`);
        break;
      }
      
      matched++;
      processed++;
      
      const remaining = fetchLimit - processed;
      console.log(`\n[${processed}/${fetchLimit}] Matched: ${ardriveFile.name} (${remaining} remaining)`);
      console.log(`  ArDrive Path: ${ardriveFile.path}`);
      console.log(`  File ID: ${ardriveFile.entityId}`);
      console.log(`  Attachment: ${attachment.file_name} (auuid: ${attachment.auuid})`);
      
      // Download and verify the file
      console.log(`  Downloading file for verification...`);
      const fileData = await downloadArDriveFile(ardriveFile.dataTxId);
      
      if (!fileData) {
        console.log(`  ✗ Failed to download file`);
        failed++;
        continue;
      }
      
      console.log(`  Downloaded ${fileData.length} bytes`);
      
      // Verify hash
      if (!verifyFileHash(fileData, attachment)) {
        console.log(`  ✗ Hash mismatch - skipping`);
        failed++;
        continue;
      }
      
      verified++;
      
      // Update database with ArDrive metadata
      try {
        // Convert values to strings and handle potential undefined/null
        // This ensures SQLite compatibility (only accepts strings, numbers, buffers, null)
        const arweaveName = String(ardriveFile.name || '');
        const arweaveId = String(ardriveFile.entityId || '');
        const arweavePath = String(ardriveFile.path || '');
        const auuid = String(attachment.auuid || '');
        
        const updateQuery = `
          UPDATE attachments
          SET arweave_file_name = ?,
              arweave_file_id = ?,
              arweave_file_path = ?,
              updated_time = CURRENT_TIMESTAMP
          WHERE auuid = ?
        `;
        
        db.prepare(updateQuery).run(
          arweaveName,
          arweaveId,
          arweavePath,
          auuid
        );
        
        console.log(`  ✓ Updated database record`);
        updated++;
        
      } catch (error) {
        console.error(`  ✗ Database update error: ${error.message}`);
        console.error(`  ArDrive file: ${ardriveFile.name}, ID: ${ardriveFile.entityId}`);
        console.error(`  Attachment: ${attachment.file_name}, auuid: ${attachment.auuid}`);
        failed++;
      }
      
      // Add delay between processing attachments (if not the last one)
      if (processed < fetchLimit && remaining > 0) {
        console.log(`  ⏱ Waiting ${fetchDelay}ms before next download...`);
        await sleep(fetchDelay);
      }
    }
    
    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('\nSummary:');
    console.log(`  Total attachments needing metadata: ${attachments.length}`);
    console.log(`  Attachments processed this run:     ${processed}`);
    console.log(`  Files matched by name:              ${matched}`);
    console.log(`  Files verified by hash:             ${verified}`);
    console.log(`  Records updated:                    ${updated}`);
    console.log(`  Failed:                             ${failed}`);
    console.log(`  Still missing metadata:             ${attachments.length - updated}`);
    
    if (processed >= fetchLimit && attachments.length > updated) {
      console.log('\n💡 Tip: Run the script again to process more attachments');
      console.log(`   ${attachments.length - updated} attachments still need metadata`);
    }
    
  } catch (error) {
    console.error('\nFatal error:', error);
    throw error;
  } finally {
    db.close();
  }
}

/**
 * Mode 2: Find and download missing attachment data
 */
async function mode2_findAttachmentData(fetchLimit = DEFAULT_FETCH_LIMIT, fetchDelay = DEFAULT_FETCH_DELAY, extraArgs = []) {
  // Load Mode 2 implementation
  const mode2 = require('./fetchpatches_mode2');
  
  console.log('='.repeat(70));
  console.log('MODE 2: Find Attachment Data');
  console.log('='.repeat(70));
  console.log();
  
  // Parse Mode 2 specific options
  const searchOptions = mode2.parseMode2Arguments(extraArgs);
  
  console.log(`Configuration:`);
  console.log(`  Search Max: ${searchOptions.searchMax} attachments per run`);
  console.log(`  Fetch Delay: ${fetchDelay}ms between each attachment`);
  console.log(`  Max File Size: ${(searchOptions.maxFileSize / (1024 * 1024)).toFixed(0)}MB`);
  console.log();
  console.log(`Search Options:`);
  console.log(`  Local Search: ${searchOptions.searchLocal ? 'Yes' : 'No'}`);
  if (searchOptions.searchLocalPaths.length > 0) {
    console.log(`  Local Paths: ${searchOptions.searchLocalPaths.join(', ')}`);
  }
  console.log(`  ArDrive: ${searchOptions.searchArDrive ? 'Yes' : 'No'}`);
  console.log(`  IPFS: ${searchOptions.searchIPFS ? 'Yes' : 'No'}`);
  console.log(`  Download URLs: ${searchOptions.searchDownload ? 'Yes' : 'No'}`);
  console.log(`  Ignore Filename: ${searchOptions.ignoreFilename ? 'Yes' : 'No'}`);
  console.log();
  
  // Check if database exists
  if (!fs.existsSync(PATCHBIN_DB_PATH)) {
    console.error(`Error: patchbin.db not found at ${PATCHBIN_DB_PATH}`);
    process.exit(1);
  }
  
  // Open database
  const db = new Database(PATCHBIN_DB_PATH);
  
  try {
    // Initialize ArDrive if needed
    let arDrive = null;
    if (searchOptions.searchArDrive || searchOptions.searchAllArDrive) {
      console.log('Initializing ArDrive client...');
      arDrive = initArDrive();
    }
    
    // Initialize and verify IPFS gateways if IPFS search is enabled
    let verifiedIPFSGateways = [];
    if (searchOptions.searchIPFS) {
      console.log('\nInitializing IPFS gateways...');
      verifiedIPFSGateways = await mode2.initializeIPFSGateways(
        searchOptions.ipfsGateways,
        db
      );
      
      if (verifiedIPFSGateways.length === 0) {
        console.log('  ⚠ No working IPFS gateways available');
        console.log('  IPFS search will be skipped');
        searchOptions.searchIPFS = false;
      }
      console.log();
    }
    
    // Query attachments needing file_data
    console.log('Querying attachments with missing file_data...');
    const query = `
      SELECT auuid, pbuuid, gvuuid, resuuid,
             file_name, file_size,
             file_hash_sha224, file_hash_sha256,
             file_ipfs_cidv0, file_ipfs_cidv1,
             arweave_file_name, arweave_file_id, arweave_file_path,
             download_urls, last_search
      FROM attachments
      WHERE file_data IS NULL
        AND (file_hash_sha224 IS NOT NULL OR file_hash_sha256 IS NOT NULL)
        AND file_size IS NOT NULL
      ORDER BY last_search ASC NULLS FIRST
      LIMIT ?
    `;
    
    const attachments = db.prepare(query).all(searchOptions.searchMax);
    console.log(`Found ${attachments.length} attachments needing file_data\n`);
    
    if (attachments.length === 0) {
      console.log('✓ No attachments need file_data!\n');
      return;
    }
    
    console.log('='.repeat(70));
    console.log('Processing attachments...\n');
    
    let processed = 0;
    let found = 0;
    let updated = 0;
    let notFound = 0;
    
    // Prepare database statements
    const updateDataStmt = db.prepare(`
      UPDATE attachments
      SET file_data = ?,
          updated_time = CURRENT_TIMESTAMP,
          last_search = CURRENT_TIMESTAMP
      WHERE auuid = ?
    `);
    
    const updateSearchStmt = db.prepare(`
      UPDATE attachments
      SET last_search = CURRENT_TIMESTAMP
      WHERE auuid = ?
    `);
    
    // Build search paths
    const searchPaths = [...mode2.DEFAULT_SEARCH_PATHS];
    if (searchOptions.searchLocalPaths.length > 0) {
      searchPaths.push(...searchOptions.searchLocalPaths);
    }
    
    // Process each attachment
    for (const attachment of attachments) {
      processed++;
      const remaining = searchOptions.searchMax - processed;
      
      console.log(`[${processed}/${searchOptions.searchMax}] ${attachment.file_name} (${remaining} remaining)`);
      console.log(`  auuid: ${attachment.auuid}`);
      console.log(`  size: ${attachment.file_size} bytes`);
      console.log(`  hashes: SHA256=${attachment.file_hash_sha256 ? 'yes' : 'no'}, SHA224=${attachment.file_hash_sha224 ? 'yes' : 'no'}`);
      
      let result = null;
      
      // Try each search option in order
      try {
        // Option A & B: Local search
        if ((searchOptions.searchLocal || searchOptions.searchLocalPaths.length > 0) && !result) {
          result = await mode2.searchLocal(attachment, searchPaths, searchOptions);
        }
        
        // Option C: ArDrive
        if (searchOptions.searchArDrive && !result && arDrive) {
          result = await mode2.searchArDrive(attachment, arDrive, searchOptions);
        }
        
        // Option D: IPFS
        if (searchOptions.searchIPFS && !result) {
          result = await mode2.searchIPFS(attachment, searchOptions, verifiedIPFSGateways);
        }
        
        // Option F: Download URLs
        if (searchOptions.searchDownload && !result) {
          result = await mode2.searchDownloadUrls(attachment, searchOptions);
        }
        
        // If found, update database
        if (result) {
          console.log(`  ✓ Found file data from: ${result.source}`);
          console.log(`    Size: ${result.data.length} bytes`);
          
          try {
            updateDataStmt.run(result.data, attachment.auuid);
            console.log(`  ✓ Updated database record\n`);
            found++;
            updated++;
          } catch (error) {
            console.error(`  ✗ Database update error: ${error.message}\n`);
          }
        } else {
          console.log(`  ✗ File not found in any source`);
          
          try {
            updateSearchStmt.run(attachment.auuid);
            console.log(`  ⏱ Updated last_search timestamp\n`);
            notFound++;
          } catch (error) {
            console.error(`  ✗ Database update error: ${error.message}\n`);
          }
        }
        
      } catch (error) {
        console.error(`  ✗ Error: ${error.message}\n`);
        // Update last_search anyway
        try {
          updateSearchStmt.run(attachment.auuid);
        } catch (e) {
          // Ignore
        }
      }
      
      // Add delay between processing
      if (processed < searchOptions.searchMax && remaining > 0) {
        console.log(`  ⏱ Waiting ${fetchDelay}ms before next search...`);
        await sleep(fetchDelay);
      }
    }
    
    // Summary
    console.log('='.repeat(70));
    console.log('\nSummary:');
    console.log(`  Total attachments checked:     ${processed}`);
    console.log(`  Files found and verified:      ${found}`);
    console.log(`  Records updated with data:     ${updated}`);
    console.log(`  Files not found:               ${notFound}`);
    
    // Check remaining
    const remainingQuery = db.prepare(`
      SELECT COUNT(*) as count 
      FROM attachments 
      WHERE file_data IS NULL 
        AND (file_hash_sha224 IS NOT NULL OR file_hash_sha256 IS NOT NULL)
        AND file_size IS NOT NULL
    `).get();
    
    console.log(`  Still missing file_data:       ${remainingQuery.count}`);
    
    if (remainingQuery.count > 0) {
      console.log('\n💡 Tip: Run the script again to process more attachments');
      console.log(`   Consider adding more search options: --searchipfs, --searchardrive, --download`);
    }
    
  } catch (error) {
    console.error('\nFatal error:', error);
    throw error;
  } finally {
    db.close();
  }
}

/**
 * Mode 3: Retrieve specific attachment (placeholder)
 */
async function mode3_retrieveAttachment(args) {
  console.log('='.repeat(70));
  console.log('MODE 3: Retrieve Attachment');
  console.log('='.repeat(70));
  console.log('\n⚠ Mode 3 not yet implemented');
  console.log('This mode will retrieve and verify a specific attachment');
  console.log('based on various identifiers (gameid, file_name, hashes, etc.).\n');
}

/**
 * Mode: Add Sizes - Populate file_size for records with file_data
 */
async function modeAddSizes() {
  console.log('='.repeat(70));
  console.log('MODE: Add Sizes');
  console.log('='.repeat(70));
  console.log();
  console.log('Populate file_size attribute for attachments with file_data\n');
  
  // Check if database exists
  if (!fs.existsSync(PATCHBIN_DB_PATH)) {
    console.error(`Error: patchbin.db not found at ${PATCHBIN_DB_PATH}`);
    process.exit(1);
  }
  
  // Open database
  const db = new Database(PATCHBIN_DB_PATH);
  
  try {
    // Check if file_size column exists
    const columns = db.prepare("PRAGMA table_info(attachments)").all();
    const hasFileSizeColumn = columns.some(col => col.name === 'file_size');
    
    if (!hasFileSizeColumn) {
      console.error('Error: file_size column does not exist in attachments table');
      console.log('\nYou may need to update the schema. Add the column with:');
      console.log('  ALTER TABLE attachments ADD COLUMN file_size INTEGER;');
      process.exit(1);
    }
    
    // Query attachments with file_data but missing file_size
    console.log('Querying attachments with file_data but missing file_size...');
    const query = `
      SELECT auuid, file_name, file_data
      FROM attachments
      WHERE file_data IS NOT NULL
        AND (file_size IS NULL OR file_size = 0)
    `;
    
    const attachments = db.prepare(query).all();
    console.log(`Found ${attachments.length} attachments needing file_size\n`);
    
    if (attachments.length === 0) {
      console.log('✓ All attachments with file_data already have file_size set!\n');
      return;
    }
    
    console.log('='.repeat(70));
    console.log('Processing attachments...\n');
    
    let updated = 0;
    let failed = 0;
    
    const updateStmt = db.prepare(`
      UPDATE attachments
      SET file_size = ?
      WHERE auuid = ?
    `);
    
    // Process each attachment
    for (let i = 0; i < attachments.length; i++) {
      const attachment = attachments[i];
      const progress = i + 1;
      const remaining = attachments.length - progress;
      
      try {
        // Get the size of file_data
        const fileSize = attachment.file_data ? attachment.file_data.length : 0;
        
        console.log(`[${progress}/${attachments.length}] ${attachment.file_name} (${remaining} remaining)`);
        console.log(`  auuid: ${attachment.auuid}`);
        console.log(`  file_size: ${fileSize} bytes`);
        
        // Update the database
        updateStmt.run(fileSize, attachment.auuid);
        
        console.log(`  ✓ Updated\n`);
        updated++;
        
      } catch (error) {
        console.error(`  ✗ Error: ${error.message}\n`);
        failed++;
      }
    }
    
    // Summary
    console.log('='.repeat(70));
    console.log('\nSummary:');
    console.log(`  Total attachments processed: ${attachments.length}`);
    console.log(`  Successfully updated:        ${updated}`);
    console.log(`  Failed:                      ${failed}`);
    
    // Verify results
    const verifyQuery = db.prepare(`
      SELECT COUNT(*) as count 
      FROM attachments 
      WHERE file_data IS NOT NULL 
        AND (file_size IS NULL OR file_size = 0)
    `).get();
    
    console.log(`  Still missing file_size:     ${verifyQuery.count}`);
    
    if (verifyQuery.count === 0) {
      console.log('\n✓ All attachments with file_data now have file_size set!');
    }
    
  } catch (error) {
    console.error('\nFatal error:', error);
    throw error;
  } finally {
    db.close();
  }
}

/**
 * Main function
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('fetchpatches.js - Fetch and manage patch attachments\n');
    console.log('Usage:');
    console.log('  node fetchpatches.js mode1 [options]          # Populate ArDrive metadata');
    console.log('  node fetchpatches.js mode2 [options]          # Find missing attachment data');
    console.log('  node fetchpatches.js mode3 [args]             # Retrieve specific attachment');
    console.log('  node fetchpatches.js addsizes                 # Populate file_size from file_data');
    console.log();
    console.log('General Options (mode1, mode2):');
    console.log(`  --fetchlimit=N    Limit attachments to process (default: ${DEFAULT_FETCH_LIMIT})`);
    console.log(`  --fetchdelay=MS   Delay between downloads (default: ${DEFAULT_FETCH_DELAY}ms, min: ${MIN_FETCH_DELAY}ms)`);
    console.log();
    console.log('Mode 2 Options:');
    console.log('  --searchmax=N              Max attachments to search (default: 20)');
    console.log('  --maxfilesize=SIZE         Max file size to download (default: 200MB)');
    console.log('  --nosearchlocal            Disable default local search');
    console.log('  --searchlocalpath=PATH     Add local search path (can repeat)');
    console.log('  --searchardrive            Search ArDrive by ID/name/path');
    console.log('  --searchipfs               Search IPFS using CIDs');
    console.log('  --ipfsgateway=URL          IPFS gateway URL (can repeat, supports %CID%)');
    console.log('  --download                 Search download_urls from database');
    console.log('  --ignorefilename           Search all files by hash only');
    console.log('  --allardrive               Broader ArDrive search');
    console.log('  --apisearch                Use private API search');
    console.log('  --apiurl=URL               API endpoint URL');
    console.log();
    console.log('Examples:');
    console.log('  node fetchpatches.js mode1');
    console.log('  node fetchpatches.js mode1 --fetchlimit=50');
    console.log('  node fetchpatches.js mode2');
    console.log('  node fetchpatches.js mode2 --searchmax=10 --searchipfs');
    console.log('  node fetchpatches.js mode2 --searchlocalpath=../backup --download');
    console.log('  node fetchpatches.js mode2 --searchipfs --ipfsgateway=https://ipfs.io/ipfs/%CID%');
    console.log('  node fetchpatches.js mode2 --searchipfs --ipfsgateway=https://gateway1.com --ipfsgateway=https://gateway2.com');
    console.log('  node fetchpatches.js addsizes');
    console.log();
    process.exit(0);
  }
  
  // Parse arguments
  const params = parseArguments(args);
  
  if (!params.mode) {
    console.error('Error: No mode specified');
    console.error('Valid modes: mode1, mode2, mode3');
    process.exit(1);
  }
  
  switch (params.mode) {
    case 'mode1':
      await mode1_populateArDriveMetadata(params.fetchLimit, params.fetchDelay);
      break;
    
    case 'mode2':
      await mode2_findAttachmentData(params.fetchLimit, params.fetchDelay, params.extraArgs);
      break;
    
    case 'mode3':
      await mode3_retrieveAttachment(params.extraArgs);
      break;
    
    case 'addsizes':
      await modeAddSizes();
      break;
    
    default:
      console.error(`Unknown mode: ${params.mode}`);
      console.error('Valid modes: mode1, mode2, mode3, addsizes');
      process.exit(1);
  }
}

// Run main function
if (require.main === module) {
  main().catch(error => {
    console.error('\nFatal error:', error);
    process.exit(1);
  });
}

module.exports = {
  mode1_populateArDriveMetadata,
  mode2_findAttachmentData,
  mode3_retrieveAttachment,
  modeAddSizes
};

