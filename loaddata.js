#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const Database = require('better-sqlite3');

/**
 * Generate a UUID v4
 */
function generateUUID() {
  return crypto.randomUUID();
}

// Database path
const DB_PATH = path.join(__dirname, 'electron', 'rhdata.db');

// Fields to check for duplicates
const DUPLICATE_CHECK_FIELDS = [
  'gameid', 'name', 'gametype', 'moderated', 'author', 'authors', 
  'submitter', 'demo', 'length', 'difficulty', 'url', 'download_url', 
  'size', 'description', 'patchblob1_name'
];

// Fields in gameversions table
const GAMEVERSION_FIELDS = [
  'section', 'gameid', 'version', 'removed', 'obsoleted', 'gametype', 
  'name', 'time', 'added', 'moderated', 'author', 'authors', 'submitter', 
  'demo', 'featured', 'length', 'difficulty', 'url', 'download_url', 
  'name_href', 'author_href', 'obsoleted_by', 'pat_sha224', 'size', 
  'description', 'gvjsondata', 'gvchange_attributes', 'gvchanges', 
  'tags', 'tags_href'
];

// Fields in patchblobs table
const PATCHBLOB_FIELDS = [
  'gvuuid', 'patch_name', 'pat_sha1', 'pat_sha224', 'pat_shake_128',
  'patchblob1_key', 'patchblob1_name', 'patchblob1_sha224',
  'result_sha1', 'result_sha224', 'result_shake1', 'pbjsondata'
];

/**
 * Check if a record with the same key fields already exists
 */
function isDuplicate(db, record) {
  const whereClauses = [];
  const params = {};
  
  DUPLICATE_CHECK_FIELDS.forEach(field => {
    if (record[field] !== undefined && record[field] !== null) {
      whereClauses.push(`${field} = @${field}`);
      params[field] = record[field];
    } else {
      whereClauses.push(`(${field} IS NULL OR ${field} = '')`);
    }
  });
  
  const query = `SELECT COUNT(*) as count FROM gameversions WHERE ${whereClauses.join(' AND ')}`;
  // Debug: uncomment to see the query
  // console.log('Duplicate check query:', query);
  // console.log('Params:', params);
  const result = db.prepare(query).get(params);
  // console.log('Duplicate check result:', result);
  return result.count > 0;
}

/**
 * Get the previous version record for the same gameid
 */
function getPreviousVersion(db, gameid) {
  const query = `
    SELECT * FROM gameversions 
    WHERE gameid = ? 
    ORDER BY version DESC 
    LIMIT 1
  `;
  return db.prepare(query).get(gameid);
}

/**
 * Find attributes that differ between two records
 */
function findChangedAttributes(prevRecord, newRecord) {
  if (!prevRecord) return null;
  
  const changed = [];
  const allKeys = new Set([...Object.keys(prevRecord), ...Object.keys(newRecord)]);
  
  // Exclude meta fields from comparison
  const excludeFields = [
    'gvuuid', 'version', 'gvjsondata', 'gvchange_attributes', 
    'gvchanges', 'gvimport_time', 'removed', 'obsoleted'
  ];
  
  allKeys.forEach(key => {
    if (excludeFields.includes(key)) return;
    
    const prevVal = prevRecord[key];
    const newVal = newRecord[key];
    
    // Compare values (handle null/undefined)
    if (JSON.stringify(prevVal) !== JSON.stringify(newVal)) {
      changed.push(key);
    }
  });
  
  return changed.length > 0 ? changed : null;
}

/**
 * Optimize JSON by removing whitespace
 */
function optimizeJSON(obj) {
  return JSON.stringify(obj);
}

/**
 * Insert a record into gameversions table
 */
function insertGameVersion(db, record) {
  const gameid = record.gameid || record.id;
  
  // Normalize the record for duplicate checking
  const normalizedRecord = {
    ...record,
    gameid: gameid,
    gametype: record.type || record.gametype
  };
  
  // Check for duplicates
  if (isDuplicate(db, normalizedRecord)) {
    console.log(`Skipping duplicate record: ${gameid} - ${record.name}`);
    return null;
  }
  
  // Get previous version if exists
  const prevVersion = getPreviousVersion(db, gameid);
  const changedAttributes = findChangedAttributes(prevVersion, record);
  
  // Prepare data for insertion
  const data = {
    gvuuid: generateUUID(),
    gameid: gameid,
    section: record.section,
    gametype: record.type || record.gametype,
    name: record.name,
    time: record.time,
    added: record.added,
    moderated: record.moderated,
    author: record.author,
    authors: record.authors,
    submitter: record.submitter,
    demo: record.demo,
    featured: record.featured,
    length: record.length,
    difficulty: record.difficulty,
    url: record.url,
    download_url: record.download_url,
    name_href: record.name_href,
    author_href: record.author_href,
    obsoleted_by: record.obsoleted_by,
    patchblob1_name: record.patchblob1_name,
    pat_sha224: record.pat_sha224,
    size: record.size,
    description: record.description,
    gvjsondata: optimizeJSON(record),
    gvchange_attributes: changedAttributes ? JSON.stringify(changedAttributes) : null,
    tags: Array.isArray(record.tags) ? JSON.stringify(record.tags) : record.tags,
    tags_href: record.tags_href
  };
  
  // Build INSERT query
  const fields = [];
  const placeholders = [];
  const values = {};
  
  Object.keys(data).forEach(key => {
    if (data[key] !== undefined) {
      fields.push(key);
      placeholders.push(`@${key}`);
      values[key] = data[key];
    }
  });
  
  const query = `
    INSERT INTO gameversions (${fields.join(', ')}) 
    VALUES (${placeholders.join(', ')})
  `;
  
  const result = db.prepare(query).run(values);
  console.log(`Inserted gameversion: ${gameid} - ${record.name} (gvuuid: ${data.gvuuid})`);
  
  return data.gvuuid;
}

/**
 * Insert a record into rhpatches table
 */
function insertRhPatch(db, gameid, patchName) {
  if (!patchName) return;
  
  try {
    const query = `
      INSERT INTO rhpatches (rhpuuid, gameid, patch_name) 
      VALUES (@rhpuuid, @gameid, @patch_name)
      ON CONFLICT(patch_name) DO NOTHING
    `;
    
    db.prepare(query).run({ 
      rhpuuid: generateUUID(),
      gameid, 
      patch_name: patchName 
    });
    console.log(`  - Inserted rhpatch: ${patchName}`);
  } catch (error) {
    console.log(`  - Skipped rhpatch (already exists): ${patchName}`);
  }
}

/**
 * Insert a record into patchblobs table
 */
function insertPatchBlob(db, gvuuid, record) {
  if (!record.patchblob1_name || !record.patchblob1_key || !record.patchblob1_sha224) {
    return;
  }
  
  const data = {
    pbuuid: generateUUID(),
    gvuuid: gvuuid,
    patch_name: record.patch,
    pat_sha1: record.pat_sha1,
    pat_sha224: record.pat_sha224,
    pat_shake_128: record.pat_shake_128,
    patchblob1_key: record.patchblob1_key,
    patchblob1_name: record.patchblob1_name,
    patchblob1_sha224: record.patchblob1_sha224,
    result_sha1: record.result_sha1,
    result_sha224: record.result_sha224,
    result_shake1: record.result_shake1,
    pbjsondata: optimizeJSON(record)
  };
  
  try {
    const fields = [];
    const placeholders = [];
    const values = {};
    
    Object.keys(data).forEach(key => {
      if (data[key] !== undefined) {
        fields.push(key);
        placeholders.push(`@${key}`);
        values[key] = data[key];
      }
    });
    
    const query = `
      INSERT INTO patchblobs (${fields.join(', ')}) 
      VALUES (${placeholders.join(', ')})
      ON CONFLICT(patchblob1_name) DO NOTHING
    `;
    
    db.prepare(query).run(values);
    console.log(`  - Inserted patchblob: ${record.patchblob1_name}`);
  } catch (error) {
    console.log(`  - Skipped patchblob (already exists): ${record.patchblob1_name}`);
  }
}

/**
 * Process a single record
 */
function processRecord(db, record) {
  const gameid = record.gameid || record.id;
  
  // Insert into gameversions
  const gvuuid = insertGameVersion(db, record);
  
  if (!gvuuid) {
    return; // Skip if duplicate
  }
  
  // Insert into rhpatches if patch attribute exists
  if (record.patch) {
    insertRhPatch(db, gameid, record.patch);
  }
  
  // Insert into patchblobs if required fields exist
  insertPatchBlob(db, gvuuid, record);
}

/**
 * Main function
 */
function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error('Usage: node loaddata.js <json-file>');
    console.error('Example: node loaddata.js electron/example-rhmd/10012');
    process.exit(1);
  }
  
  const jsonFile = args[0];
  
  // Check if file exists
  if (!fs.existsSync(jsonFile)) {
    console.error(`Error: File not found: ${jsonFile}`);
    process.exit(1);
  }
  
  // Read JSON file
  let data;
  try {
    const content = fs.readFileSync(jsonFile, 'utf8');
    data = JSON.parse(content);
  } catch (error) {
    console.error(`Error reading JSON file: ${error.message}`);
    process.exit(1);
  }
  
  // Check if database exists
  if (!fs.existsSync(DB_PATH)) {
    console.error(`Error: Database not found: ${DB_PATH}`);
    process.exit(1);
  }
  
  // Open database
  const db = new Database(DB_PATH);
  
  // Enable foreign keys (but we'll handle the constraints manually if needed)
  db.pragma('foreign_keys = OFF');
  
  try {
    // Process data (single object or array)
    const records = Array.isArray(data) ? data : [data];
    
    console.log(`Processing ${records.length} record(s)...`);
    
    records.forEach((record, index) => {
      console.log(`\n[${index + 1}/${records.length}] Processing record...`);
      processRecord(db, record);
    });
    
    console.log('\nDone!');
  } finally {
    db.close();
  }
}

// Run main function
if (require.main === module) {
  main();
}

