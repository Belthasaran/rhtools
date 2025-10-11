-- Digital Signature Schema for Metadata Records
-- Supports RSA and ED25519 signatures

-- Signature Lists Table
-- Each signed record references a signaturelist
CREATE TABLE IF NOT EXISTS signaturelists (
  siglistuuid VARCHAR(255) PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  record_type VARCHAR(255),
  record_uuid VARCHAR(255)
);

-- Signature List Entries Table
-- Contains actual signatures for each record
CREATE TABLE IF NOT EXISTS signaturelistentries (
  entryuuid VARCHAR(255) PRIMARY KEY,
  siglistuuid VARCHAR(255),
  signeruuid VARCHAR(255),
  signature TEXT NOT NULL,
  signature_algorithm VARCHAR(255) DEFAULT 'ED25519',
  hash_algorithm VARCHAR(255) DEFAULT 'SHA256',
  signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(siglistuuid) REFERENCES signaturelists(siglistuuid),
  FOREIGN KEY(signeruuid) REFERENCES signers(signeruuid),
  UNIQUE(siglistuuid, signeruuid)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_signaturelistentries_siglistuuid 
  ON signaturelistentries(siglistuuid);

CREATE INDEX IF NOT EXISTS idx_signaturelistentries_signeruuid 
  ON signaturelistentries(signeruuid);

-- Add siglistuuid column to tables that need signatures
-- Note: Run these only if columns don't exist

-- ALTER TABLE gameversions ADD COLUMN siglistuuid VARCHAR(255) REFERENCES signaturelists(siglistuuid);
-- ALTER TABLE patchblobs ADD COLUMN siglistuuid VARCHAR(255) REFERENCES signaturelists(siglistuuid);
-- ALTER TABLE rhpatches ADD COLUMN siglistuuid VARCHAR(255) REFERENCES signaturelists(siglistuuid);
-- ALTER TABLE attachments ADD COLUMN siglistuuid VARCHAR(255) REFERENCES signaturelists(siglistuuid);

