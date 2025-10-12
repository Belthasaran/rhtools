/**
 * record-creator.js - Database Record Creation
 * 
 * Creates gameversions, patchblobs, and attachments records
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const Database = require('better-sqlite3');
const crc32 = require('crc-32');
const { crc16 } = require('crc');
const { CID } = require('multiformats/cid');
const { sha256 } = require('multiformats/hashes/sha2');
const fernet = require('fernet');
const lzma = require('lzma-native');
const UrlBase64 = require('urlsafe-base64');

class RecordCreator {
  constructor(dbManager, patchbinDbPath, config) {
    this.dbManager = dbManager;
    this.config = config;
    
    // Open patchbin database
    this.patchbinDb = new Database(patchbinDbPath);
    this.patchbinDb.pragma('foreign_keys = OFF');
  }
  
  /**
   * Create complete set of records for a processed game
   */
  async createGameRecords(queueItem, patchFiles) {
    const gameid = queueItem.gameid;
    console.log(`  Creating records for game ${gameid}...`);
    
    // Parse metadata
    const metadata = typeof queueItem.game_metadata === 'string'
      ? JSON.parse(queueItem.game_metadata)
      : queueItem.game_metadata;
    
    // Filter successful patches
    const successfulPatches = patchFiles.filter(p => p.status === 'completed' && p.blob_data);
    
    if (successfulPatches.length === 0) {
      console.log(`    ⚠ No successful patches with blobs, skipping`);
      return null;
    }
    
    // Find primary patch
    const primaryPatch = successfulPatches.find(p => p.is_primary === 1) || successfulPatches[0];
    const primaryBlobData = JSON.parse(primaryPatch.blob_data);
    
    this.dbManager.beginTransaction();
    
    try {
      // 1. Create gameversion record
      const gvuuid = await this.createGameVersionRecord(
        gameid,
        metadata,
        primaryPatch,
        primaryBlobData
      );
      
      console.log(`    ✓ Gameversion created: ${gvuuid}`);
      
      // 2. Create patchblob records (one per patch)
      const patchblobRecords = [];
      for (const patchFile of successfulPatches) {
        const blobData = JSON.parse(patchFile.blob_data);
        
        const pbuuid = await this.createPatchBlobRecord(
          gvuuid,
          gameid,
          patchFile,
          blobData
        );
        
        patchblobRecords.push({ pbuuid, patchFile, blobData });
        console.log(`    ✓ Patchblob created: ${pbuuid}`);
      }
      
      // 3. Create attachment records
      for (const pbRecord of patchblobRecords) {
        await this.createAttachmentRecord(
          pbRecord.pbuuid,
          gvuuid,
          pbRecord.blobData
        );
        console.log(`    ✓ Attachment created for ${pbRecord.blobData.patchblob1_name}`);
      }
      
      this.dbManager.commit();
      
      console.log(`    ✓ All records created successfully`);
      
      return { gvuuid, patchblobRecords };
      
    } catch (error) {
      this.dbManager.rollback();
      console.error(`    ✗ Error creating records: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * Create gameversion record
   */
  async createGameVersionRecord(gameid, metadata, primaryPatch, primaryBlobData) {
    // Get previous version to check for changes
    const previousVersion = this.dbManager.getLatestVersionForGame(gameid);
    const nextVersion = previousVersion ? (previousVersion.version || 0) + 1 : 1;
    
    // Find changed attributes
    let changedAttributes = null;
    if (previousVersion) {
      changedAttributes = this.findChangedFields(previousVersion, metadata);
    }
    
    const data = {
      gvuuid: this.generateUUID(),
      gameid: gameid,
      version: nextVersion,
      section: metadata.section || null,
      gametype: metadata.type || metadata.gametype || metadata.difficulty || null,
      name: metadata.name || null,
      time: metadata.time || null,
      added: metadata.added || null,
      moderated: metadata.moderated || null,
      author: metadata.author || null,
      authors: metadata.authors || null,
      submitter: metadata.submitter || null,
      demo: metadata.demo || null,
      featured: metadata.featured || null,
      length: metadata.length || null,
      difficulty: metadata.difficulty || null,
      url: metadata.url || null,
      download_url: metadata.download_url || null,
      name_href: metadata.name_href || null,
      author_href: metadata.author_href || null,
      obsoleted_by: metadata.obsoleted_by || null,
      size: metadata.size || null,
      description: metadata.description || null,
      tags: Array.isArray(metadata.tags) ? JSON.stringify(metadata.tags) : metadata.tags,
      tags_href: metadata.tags_href || null,
      gvjsondata: JSON.stringify(metadata),
      gvchange_attributes: changedAttributes ? JSON.stringify(changedAttributes) : null,
      
      // Primary patch information
      patchblob1_name: primaryBlobData.patchblob1_name || null,
      pat_sha224: primaryPatch.pat_sha224 || null,
      
      removed: metadata.removed || 0,
      obsoleted: metadata.obsoleted || 0
    };
    
    this.dbManager.createGameVersion(data);
    
    return data.gvuuid;
  }
  
  /**
   * Find changed fields between old and new record
   */
  findChangedFields(oldRecord, newMetadata) {
    const compareFields = [
      'name', 'author', 'authors', 'description', 'difficulty',
      'length', 'demo', 'featured', 'url', 'download_url', 
      'gametype', 'type', 'size'
    ];
    
    const changed = [];
    
    // Parse old JSON data
    let oldData = {};
    if (oldRecord.gvjsondata) {
      try {
        oldData = JSON.parse(oldRecord.gvjsondata);
      } catch (error) {
        // Use record fields directly
        oldData = oldRecord;
      }
    } else {
      oldData = oldRecord;
    }
    
    for (const field of compareFields) {
      const oldVal = oldData[field];
      const newVal = newMetadata[field];
      
      // Normalize for comparison
      const oldNorm = this.normalizeValue(oldVal);
      const newNorm = this.normalizeValue(newVal);
      
      if (JSON.stringify(oldNorm) !== JSON.stringify(newNorm)) {
        changed.push(field);
      }
    }
    
    return changed.length > 0 ? changed : null;
  }
  
  /**
   * Normalize value for comparison
   */
  normalizeValue(val) {
    if (val === null || val === undefined || val === '') {
      return null;
    }
    return val;
  }
  
  /**
   * Create patchblob record
   */
  async createPatchBlobRecord(gvuuid, gameid, patchFile, blobData) {
    // Check if identical patchblob already exists
    const existing = this.dbManager.getPatchBlobByHashes(
      patchFile.pat_sha224,
      patchFile.result_sha224
    );
    
    if (existing) {
      console.log(`      ⓘ Patchblob already exists (${existing.pbuuid}), reusing`);
      
      // Link to this gameversion
      this.dbManager.linkPatchBlobToGameVersion(existing.pbuuid, gvuuid);
      
      return existing.pbuuid;
    }
    
    // Create new patchblob
    const data = {
      pbuuid: this.generateUUID(),
      gvuuid: gvuuid,
      patch_name: patchFile.patch_filename || null,
      pat_sha1: patchFile.pat_sha1 || null,
      pat_sha224: patchFile.pat_sha224 || null,
      pat_shake_128: patchFile.pat_shake_128 || null,
      result_sha1: patchFile.result_sha1 || null,
      result_sha224: patchFile.result_sha224 || null,
      result_shake1: patchFile.result_shake1 || null,
      patchblob1_key: blobData.patchblob1_key || null,
      patchblob1_name: blobData.patchblob1_name || null,
      patchblob1_sha224: blobData.patchblob1_sha224 || null,
      pbjsondata: JSON.stringify({
        ...patchFile,
        ...blobData
      }),
      
      // Extended fields
      patch_filename: patchFile.patch_filename || null,
      patch_type: patchFile.patch_type || null,
      is_primary: patchFile.is_primary || 0,
      zip_source: patchFile.zip_path || null
    };
    
    this.dbManager.createPatchBlob(data);
    
    return data.pbuuid;
  }
  
  /**
   * Create attachment record (in patchbin.db)
   */
  async createAttachmentRecord(pbuuid, gvuuid, blobData) {
    // Check if attachment with same hash already exists
    const existing = this.patchbinDb.prepare(`
      SELECT auuid, parents FROM attachments 
      WHERE file_name = ? AND file_hash_sha224 = ?
    `).get(blobData.patchblob1_name, blobData.patchblob1_sha224);
    
    if (existing) {
      console.log(`      ⓘ Attachment already exists (${existing.auuid})`);
      
      // Update parents array to include this pbuuid
      const parents = JSON.parse(existing.parents || '[]');
      if (!parents.includes(pbuuid)) {
        parents.push(pbuuid);
        this.patchbinDb.prepare(`
          UPDATE attachments 
          SET parents = ?
          WHERE auuid = ?
        `).run(JSON.stringify(parents), existing.auuid);
      }
      
      return existing.auuid;
    }
    
    // Read blob file
    const blobPath = path.join(this.config.BLOBS_DIR, blobData.patchblob1_name);
    
    if (!fs.existsSync(blobPath)) {
      throw new Error(`Blob file not found: ${blobPath}`);
    }
    
    const fileData = fs.readFileSync(blobPath);
    
    // Calculate all hashes and checksums
    const fileSha1 = crypto.createHash('sha1').update(fileData).digest('hex');
    const fileSha224 = crypto.createHash('sha224').update(fileData).digest('hex');
    const fileSha256 = crypto.createHash('sha256').update(fileData).digest('hex');
    const fileMd5 = crypto.createHash('md5').update(fileData).digest('hex');
    const fileCrc16 = this.calculateCRC16(fileData);
    const fileCrc32 = this.calculateCRC32(fileData);
    
    // Calculate IPFS CIDs
    const { cidv0, cidv1 } = await this.calculateIPFSCIDs(fileData);
    
    // Decode and calculate decoded hashes
    let decodedData = null;
    let decodedSha1 = '';
    let decodedSha224 = '';
    let decodedSha256 = '';
    let decodedMd5 = '';
    let decodedCidv0 = '';
    let decodedCidv1 = '';
    
    if (blobData.patchblob1_key) {
      try {
        decodedData = await this.decodeBlob(fileData, blobData.patchblob1_key);
        
        decodedSha1 = crypto.createHash('sha1').update(decodedData).digest('hex');
        decodedSha224 = crypto.createHash('sha224').update(decodedData).digest('hex');
        decodedSha256 = crypto.createHash('sha256').update(decodedData).digest('hex');
        decodedMd5 = crypto.createHash('md5').update(decodedData).digest('hex');
        
        const decodedCids = await this.calculateIPFSCIDs(decodedData);
        decodedCidv0 = decodedCids.cidv0;
        decodedCidv1 = decodedCids.cidv1;
      } catch (error) {
        console.warn(`      ⚠ Failed to decode blob: ${error.message}`);
      }
    }
    
    const data = {
      auuid: this.generateUUID(),
      pbuuid: pbuuid,
      gvuuid: gvuuid,
      file_crc16: fileCrc16,
      file_crc32: fileCrc32,
      file_size: fileData.length,
      locators: JSON.stringify([]),
      parents: JSON.stringify([pbuuid]),
      file_ipfs_cidv0: cidv0,
      file_ipfs_cidv1: cidv1,
      file_hash_sha224: fileSha224,
      file_hash_sha1: fileSha1,
      file_hash_md5: fileMd5,
      file_hash_sha256: fileSha256,
      file_name: blobData.patchblob1_name,
      filekey: blobData.patchblob1_key || '',
      decoded_ipfs_cidv0: decodedCidv0,
      decoded_ipfs_cidv1: decodedCidv1,
      decoded_hash_sha224: decodedSha224,
      decoded_hash_sha1: decodedSha1,
      decoded_hash_md5: decodedMd5,
      decoded_hash_sha256: decodedSha256,
      file_data: fileData
    };
    
    const fields = Object.keys(data);
    const placeholders = fields.map(f => `@${f}`);
    
    this.patchbinDb.prepare(`
      INSERT INTO attachments (${fields.join(', ')})
      VALUES (${placeholders.join(', ')})
    `).run(data);
    
    return data.auuid;
  }
  
  /**
   * Calculate CRC16
   */
  calculateCRC16(buffer) {
    return crc16(buffer).toString(16).padStart(4, '0');
  }
  
  /**
   * Calculate CRC32
   */
  calculateCRC32(buffer) {
    const result = crc32.buf(buffer);
    return (result >>> 0).toString(16).padStart(8, '0');
  }
  
  /**
   * Calculate IPFS CIDs
   */
  async calculateIPFSCIDs(buffer) {
    const hash = await sha256.digest(buffer);
    const cidV0 = CID.createV0(hash);
    const cidV1 = CID.createV1(0x70, hash);
    
    return {
      cidv0: cidV0.toString(),
      cidv1: cidV1.toString()
    };
  }
  
  /**
   * Decode encrypted blob
   */
  async decodeBlob(encryptedData, keyBase64) {
    // Step 1: Decompress LZMA
    const decompressed1 = await new Promise((resolve, reject) => {
      lzma.decompress(encryptedData, (result, error) => {
        if (error) reject(error);
        else resolve(Buffer.from(result));
      });
    });
    
    // Step 2: Decrypt Fernet
    const key = UrlBase64.encode(Buffer.from(keyBase64, 'base64')).toString();
    const frnsecret = new fernet.Secret(key);
    const token = new fernet.Token({ 
      secret: frnsecret, 
      ttl: 0, 
      token: decompressed1.toString()
    });
    const decrypted = token.decode();
    
    // Step 3: Decompress again
    const decompressed2 = await new Promise((resolve, reject) => {
      lzma.decompress(Buffer.from(decrypted, 'base64'), (result, error) => {
        if (error) reject(error);
        else resolve(Buffer.from(result));
      });
    });
    
    return decompressed2;
  }
  
  /**
   * Generate UUID
   */
  generateUUID() {
    return crypto.randomUUID();
  }
  
  /**
   * Close databases
   */
  close() {
    this.patchbinDb.close();
  }
}

module.exports = RecordCreator;

