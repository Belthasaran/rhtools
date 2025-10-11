#!/usr/bin/env node

/**
 * Sign Metadata Records
 * 
 * Creates digital signatures for records in gameversions, patchblobs, rhpatches, attachments
 * 
 * Usage:
 *   node sign_metadata.js --signer=SIGNER_UUID --table=TABLE_NAME --record=RECORD_UUID --keyfile=KEY_FILE
 *   node sign_metadata.js --signer=abc123 --table=attachments --record=xyz789 --keyfile=signer_metadata_abc_2025.txt
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const PATCHBIN_DB = path.join(__dirname, 'patchbin.db');
const RHDATA_DB = path.join(__dirname, 'rhdata.db');

// Tables that support signatures
const SIGNED_TABLES = {
  'gameversions': { db: RHDATA_DB, primaryKey: 'gvuuid' },
  'patchblobs': { db: RHDATA_DB, primaryKey: 'pbuuid' },
  'rhpatches': { db: RHDATA_DB, primaryKey: 'rhpuuid' },
  'attachments': { db: PATCHBIN_DB, primaryKey: 'auuid' }
};

/**
 * Parse key file
 */
function parseKeyFile(keyfilePath) {
  const content = fs.readFileSync(keyfilePath, 'utf8');
  
  const signerUuid = content.match(/SIGNER_UUID=([^\n]+)/)?.[1];
  const algorithm = content.match(/ALGORITHM=([^\n]+)/)?.[1];
  
  // Extract PEM private key
  const pemMatch = content.match(/PRIVATE_KEY_PEM<<EOF\n([\s\S]+?)\nEOF/);
  const privateKeyPem = pemMatch ? pemMatch[1] : null;
  
  // Or hex private key
  const privateKeyHex = content.match(/PRIVATE_KEY_HEX=([^\n]+)/)?.[1];
  
  if (!signerUuid || !algorithm) {
    throw new Error('Invalid key file format');
  }
  
  let privateKey;
  if (privateKeyPem) {
    privateKey = crypto.createPrivateKey(privateKeyPem);
  } else if (privateKeyHex) {
    const keyBuffer = Buffer.from(privateKeyHex, 'hex');
    privateKey = crypto.createPrivateKey({
      key: keyBuffer,
      format: 'der',
      type: 'pkcs8'
    });
  } else {
    throw new Error('No private key found in file');
  }
  
  return {
    signerUuid,
    algorithm,
    privateKey
  };
}

/**
 * Get record from database
 */
function getRecord(tableName, recordUuid) {
  const tableInfo = SIGNED_TABLES[tableName];
  if (!tableInfo) {
    throw new Error(`Table ${tableName} is not a signed table`);
  }
  
  const db = new Database(tableInfo.db);
  
  try {
    const record = db.prepare(`SELECT * FROM ${tableName} WHERE ${tableInfo.primaryKey} = ?`).get(recordUuid);
    
    if (!record) {
      throw new Error(`Record not found: ${recordUuid}`);
    }
    
    return record;
  } finally {
    db.close();
  }
}

/**
 * Create canonical string for signing
 * Excludes: siglistuuid, signature fields, timestamps with 'import' or 'updated' in name
 */
function createCanonicalString(record) {
  const entries = Object.entries(record)
    .filter(([key, value]) => {
      // Exclude signature-related fields
      if (key === 'siglistuuid') return false;
      if (key.includes('signature')) return false;
      if (key.includes('import_time')) return false;
      if (key.includes('updated_time')) return false;
      if (key.includes('gvimport_time')) return false;
      if (key.includes('pbimport_time')) return false;
      
      return true;
    })
    .sort(([a], [b]) => a.localeCompare(b)); // Sort by key name
  
  // Create canonical string
  const parts = entries.map(([key, value]) => {
    if (value === null) {
      return `${key}=null`;
    } else if (Buffer.isBuffer(value)) {
      // For binary data, use hex representation
      return `${key}=${value.toString('hex')}`;
    } else {
      return `${key}=${value}`;
    }
  });
  
  return parts.join('&');
}

/**
 * Sign data
 */
function signData(data, privateKey, algorithm) {
  const hash = crypto.createHash('sha256').update(data).digest();
  
  if (algorithm === 'ED25519') {
    const signature = crypto.sign(null, hash, privateKey);
    return signature.toString('hex');
  } else if (algorithm === 'RSA') {
    const signature = crypto.sign('sha256', hash, {
      key: privateKey,
      padding: crypto.constants.RSA_PKCS1_PSS_PADDING
    });
    return signature.toString('hex');
  } else {
    throw new Error(`Unsupported algorithm: ${algorithm}`);
  }
}

/**
 * Create or get signaturelist for record
 */
function ensureSignatureList(db, tableName, recordUuid, currentSiglistUuid) {
  if (currentSiglistUuid) {
    return currentSiglistUuid;
  }
  
  // Create new signaturelist
  const siglistUuid = crypto.randomUUID();
  
  db.prepare(`
    INSERT INTO signaturelists (siglistuuid, record_type, record_uuid)
    VALUES (?, ?, ?)
  `).run(siglistUuid, tableName, recordUuid);
  
  console.log(`  ✓ Created new signaturelist: ${siglistUuid}`);
  
  return siglistUuid;
}

/**
 * Add signature to signaturelist
 */
function addSignature(db, siglistUuid, signerUuid, signature, algorithm) {
  // Check if signature already exists for this signer
  const existing = db.prepare(`
    SELECT entryuuid FROM signaturelistentries
    WHERE siglistuuid = ? AND signeruuid = ?
  `).get(siglistUuid, signerUuid);
  
  if (existing) {
    console.log(`  ⚠ Signature already exists for this signer, updating...`);
    
    db.prepare(`
      UPDATE signaturelistentries
      SET signature = ?, signed_at = CURRENT_TIMESTAMP
      WHERE entryuuid = ?
    `).run(signature, existing.entryuuid);
    
    console.log(`  ✓ Updated signature`);
  } else {
    const entryUuid = crypto.randomUUID();
    
    db.prepare(`
      INSERT INTO signaturelistentries (entryuuid, siglistuuid, signeruuid, signature, signature_algorithm, hash_algorithm)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(entryUuid, siglistUuid, signerUuid, signature, algorithm, 'SHA256');
    
    console.log(`  ✓ Created new signature entry: ${entryUuid}`);
  }
}

/**
 * Update record with siglistuuid
 */
function updateRecordSiglistUuid(tableName, recordUuid, siglistUuid) {
  const tableInfo = SIGNED_TABLES[tableName];
  const db = new Database(tableInfo.db);
  
  try {
    // Check if siglistuuid column exists
    const columns = db.prepare(`PRAGMA table_info(${tableName})`).all();
    const hasSiglistUuid = columns.some(col => col.name === 'siglistuuid');
    
    if (!hasSiglistUuid) {
      console.log(`  ⚠ Warning: ${tableName} table does not have siglistuuid column`);
      console.log(`  Run: ALTER TABLE ${tableName} ADD COLUMN siglistuuid VARCHAR(255);`);
      return false;
    }
    
    db.prepare(`
      UPDATE ${tableName}
      SET siglistuuid = ?
      WHERE ${tableInfo.primaryKey} = ?
    `).run(siglistUuid, recordUuid);
    
    console.log(`  ✓ Updated ${tableName} record with siglistuuid`);
    return true;
  } finally {
    db.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  
  // Parse arguments
  const options = {};
  for (const arg of args) {
    if (arg.startsWith('--')) {
      const [key, value] = arg.substring(2).split('=');
      options[key] = value;
    }
  }
  
  if (!options.table || !options.record || !options.keyfile) {
    console.log('Sign Metadata Records\n');
    console.log('Usage:');
    console.log('  node sign_metadata.js --table=TABLE_NAME --record=RECORD_UUID --keyfile=KEY_FILE');
    console.log();
    console.log('Options:');
    console.log('  --table=NAME      Table name (gameversions, patchblobs, rhpatches, attachments)');
    console.log('  --record=UUID     Record UUID to sign');
    console.log('  --keyfile=PATH    Path to signer key file');
    console.log('  --signer=UUID     (Optional) Signer UUID (read from keyfile if not provided)');
    console.log();
    console.log('Example:');
    console.log('  node sign_metadata.js --table=attachments --record=abc-123 --keyfile=signer_metadata_abc.txt');
    console.log();
    process.exit(0);
  }
  
  console.log('='.repeat(70));
  console.log('Signing Metadata Record');
  console.log('='.repeat(70));
  console.log();
  
  const tableName = options.table;
  const recordUuid = options.record;
  const keyfilePath = path.resolve(options.keyfile);
  
  console.log(`Table:   ${tableName}`);
  console.log(`Record:  ${recordUuid}`);
  console.log(`Keyfile: ${keyfilePath}`);
  console.log();
  
  // Load signer key
  console.log('Loading signer key...');
  const signer = parseKeyFile(keyfilePath);
  console.log(`  ✓ Loaded ${signer.algorithm} private key`);
  console.log(`  Signer UUID: ${signer.signerUuid}`);
  console.log();
  
  // Get record from database
  console.log('Loading record from database...');
  const record = getRecord(tableName, recordUuid);
  console.log(`  ✓ Found record in ${tableName}`);
  console.log();
  
  // Create canonical string
  console.log('Creating canonical string...');
  const canonical = createCanonicalString(record);
  console.log(`  ✓ Canonical string created (${canonical.length} bytes)`);
  console.log();
  
  // Sign the data
  console.log('Generating signature...');
  const signature = signData(canonical, signer.privateKey, signer.algorithm);
  console.log(`  ✓ Signature generated (${signature.length} hex chars)`);
  console.log(`    ${signature.substring(0, 64)}...`);
  console.log();
  
  // Open patchbin.db for signature management
  const db = new Database(PATCHBIN_DB);
  
  try {
    // Ensure signaturelists and signaturelistentries tables exist
    const schemaPath = path.join(__dirname, 'signatures_schema.sql');
    if (fs.existsSync(schemaPath)) {
      const schema = fs.readFileSync(schemaPath, 'utf8');
      db.exec(schema);
    }
    
    // Ensure signaturelist exists for this record
    console.log('Managing signature list...');
    const siglistUuid = ensureSignatureList(db, tableName, recordUuid, record.siglistuuid);
    
    // Add signature to signaturelist
    addSignature(db, siglistUuid, signer.signerUuid, signature, signer.algorithm);
    
    // Update record with siglistuuid if it was null
    if (!record.siglistuuid) {
      updateRecordSiglistUuid(tableName, recordUuid, siglistUuid);
    }
    
    console.log();
    console.log('='.repeat(70));
    console.log('Signature Created Successfully!');
    console.log('='.repeat(70));
    console.log();
    console.log(`Record:        ${recordUuid}`);
    console.log(`Table:         ${tableName}`);
    console.log(`Signature List: ${siglistUuid}`);
    console.log(`Signer:        ${signer.signerUuid}`);
    console.log(`Algorithm:     ${signer.algorithm}`);
    console.log(`Signature:     ${signature.substring(0, 32)}...`);
    console.log();
    
    // Show current signatures for this record
    const signatures = db.prepare(`
      SELECT e.*, s.signer_name, s.publickey_type
      FROM signaturelistentries e
      JOIN signers s ON e.signeruuid = s.signeruuid
      WHERE e.siglistuuid = ?
      ORDER BY e.signed_at DESC
    `).all(siglistUuid);
    
    console.log(`Total signatures for this record: ${signatures.length}`);
    signatures.forEach((sig, idx) => {
      console.log(`  ${idx+1}. ${sig.signer_name} (${sig.publickey_type}) - ${sig.signed_at}`);
    });
    console.log();
    
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  } finally {
    db.close();
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error.message);
    process.exit(1);
  });
}

module.exports = { createCanonicalString, signData };

