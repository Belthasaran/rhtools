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
const DEFAULT_FETCH_DELAY = 2000; // milliseconds
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
 * Mode 2: Find and download missing attachment data (placeholder)
 */
async function mode2_findAttachmentData(fetchLimit = DEFAULT_FETCH_LIMIT, fetchDelay = DEFAULT_FETCH_DELAY) {
  console.log('='.repeat(70));
  console.log('MODE 2: Find Attachment Data');
  console.log('='.repeat(70));
  console.log();
  console.log(`Configuration:`);
  console.log(`  Fetch Limit: ${fetchLimit} attachments per run`);
  console.log(`  Fetch Delay: ${fetchDelay}ms between each attachment`);
  console.log();
  console.log('⚠ Mode 2 not yet implemented');
  console.log('This mode will search for and download missing file_data');
  console.log('from local filesystem, ArDrive, and IPFS.\n');
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
    console.log();
    console.log('Options for modes that query remote servers (mode1, mode2):');
    console.log(`  --fetchlimit=N    Limit number of attachments to process (default: ${DEFAULT_FETCH_LIMIT})`);
    console.log(`  --fetchdelay=MS   Delay in milliseconds between downloads (default: ${DEFAULT_FETCH_DELAY}ms, min: ${MIN_FETCH_DELAY}ms)`);
    console.log();
    console.log('Examples:');
    console.log('  node fetchpatches.js mode1');
    console.log('  node fetchpatches.js mode1 --fetchlimit=50 --fetchdelay=1000');
    console.log('  node fetchpatches.js mode1 --fetchlimit=100');
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
      await mode2_findAttachmentData(params.fetchLimit, params.fetchDelay);
      break;
    
    case 'mode3':
      await mode3_retrieveAttachment(params.extraArgs);
      break;
    
    default:
      console.error(`Unknown mode: ${params.mode}`);
      console.error('Valid modes: mode1, mode2, mode3');
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
  mode3_retrieveAttachment
};

