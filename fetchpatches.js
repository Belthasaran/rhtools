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
async function mode1_populateArDriveMetadata() {
  console.log('='.repeat(70));
  console.log('MODE 1: Populate ArDrive Metadata');
  console.log('='.repeat(70));
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
      
      matched++;
      console.log(`\n[${matched}] Matched: ${ardriveFile.name}`);
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
    }
    
    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('\nSummary:');
    console.log(`  Total attachments checked: ${attachments.length}`);
    console.log(`  Files matched by name:     ${matched}`);
    console.log(`  Files verified by hash:    ${verified}`);
    console.log(`  Records updated:           ${updated}`);
    console.log(`  Failed:                    ${failed}`);
    console.log(`  Still missing metadata:    ${attachments.length - updated}`);
    
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
async function mode2_findAttachmentData() {
  console.log('='.repeat(70));
  console.log('MODE 2: Find Attachment Data');
  console.log('='.repeat(70));
  console.log('\n⚠ Mode 2 not yet implemented');
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
    console.log('  node fetchpatches.js mode1          # Populate ArDrive metadata');
    console.log('  node fetchpatches.js mode2          # Find missing attachment data');
    console.log('  node fetchpatches.js mode3 [args]   # Retrieve specific attachment');
    console.log();
    process.exit(0);
  }
  
  const mode = args[0].toLowerCase();
  
  switch (mode) {
    case 'mode1':
      await mode1_populateArDriveMetadata();
      break;
    
    case 'mode2':
      await mode2_findAttachmentData();
      break;
    
    case 'mode3':
      await mode3_retrieveAttachment(args.slice(1));
      break;
    
    default:
      console.error(`Unknown mode: ${mode}`);
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

