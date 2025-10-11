
CREATE TABLE csettings (
	 csettinguid varchar(255),
	 csetting_name varchar(255),
	 csetting_value text NOT NULL,
	 csetting_binary blob,
	primary  key(csettinguid)
	unique(csetting_name)
);

-- API Servers table for storing metadata API server credentials
-- Credentials are encrypted using AES-256-CBC with RHTCLIENT_VAULT_KEY
-- TODO: Move encryption key storage to OS-specific secure keychain
--       (e.g., Windows Credential Manager, macOS Keychain, Linux Secret Service)
CREATE TABLE apiservers (
	apiserveruuid VARCHAR(255) PRIMARY KEY,
	server_name VARCHAR(255),
	api_url TEXT NOT NULL,
	encrypted_clientid TEXT,
	encrypted_clientsecret TEXT,
	is_active INTEGER DEFAULT 1,
	last_used TIMESTAMP,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	notes TEXT
);
