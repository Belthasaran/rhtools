/**
 * flips-finder.js - Locate Flips Binary
 * 
 * DEPRECATED: This module is maintained for backwards compatibility.
 * Please use binary-finder.js for new code.
 * 
 * This module re-exports flips-finding functionality from binary-finder.js
 */

// Re-export from binary-finder for backwards compatibility
const { 
  BinaryFinder: BinaryFinderBase, 
  getFlipsPath, 
  findFlips 
} = require('./binary-finder');

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const Database = require('better-sqlite3');

class FlipsFinder {
  constructor(options = {}) {
    this.projectRoot = options.projectRoot || process.cwd();
    this.clientDbPath = options.clientDbPath || path.join(this.projectRoot, 'electron', 'clientdata.db');
    this.platform = process.platform;
    this.isWindows = this.platform === 'win32';
    this.executableName = this.isWindows ? 'flips.exe' : 'flips';
  }

  /**
   * Find flips binary by checking all known locations
   * Returns absolute path to flips binary or null if not found
   */
  findFlips() {
    const checks = [
      { name: 'Database setting', fn: () => this.checkDatabase() },
      { name: 'Environment variable', fn: () => this.checkEnvironment() },
      { name: 'Current directory', fn: () => this.checkCurrentDirectory() },
      { name: 'Script directory', fn: () => this.checkScriptDirectory() },
      { name: 'Common directories', fn: () => this.checkCommonDirectories() },
      { name: 'System PATH', fn: () => this.checkSystemPath() },
    ];

    for (const check of checks) {
      try {
        const result = check.fn();
        if (result && this.validateFlipsBinary(result)) {
          console.log(`  ✓ Found flips via ${check.name}: ${result}`);
          return result;
        }
      } catch (error) {
        // Silently continue to next check
      }
    }

    return null;
  }

  /**
   * Check clientdata.db for flips path setting
   */
  checkDatabase() {
    if (!fs.existsSync(this.clientDbPath)) {
      return null;
    }

    try {
      const db = new Database(this.clientDbPath, { readonly: true, fileMustExist: true });
      
      // Check if csettings table exists
      const tableExists = db.prepare(`
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='csettings'
      `).get();

      if (!tableExists) {
        db.close();
        return null;
      }

      // Query for flips path settings
      const possibleSettings = [
        'flips_path',
        'flips_bin_path',
        'FLIPS_PATH',
        'FLIPS_BIN_PATH'
      ];

      for (const settingName of possibleSettings) {
        const row = db.prepare(`
          SELECT csetting_value FROM csettings 
          WHERE csetting_name = ?
        `).get(settingName);

        if (row && row.csetting_value) {
          db.close();
          return row.csetting_value;
        }
      }

      db.close();
      return null;

    } catch (error) {
      // Database error, continue to next method
      return null;
    }
  }

  /**
   * Check FLIPS_BIN_PATH environment variable
   */
  checkEnvironment() {
    const envPath = process.env.FLIPS_BIN_PATH;
    if (envPath) {
      return envPath;
    }
    return null;
  }

  /**
   * Check current working directory
   */
  checkCurrentDirectory() {
    const cwd = process.cwd();
    const flipsPath = path.join(cwd, this.executableName);
    
    if (fs.existsSync(flipsPath)) {
      return flipsPath;
    }

    // Also check with ./ prefix
    const relativePath = path.join(cwd, '.', this.executableName);
    if (fs.existsSync(relativePath)) {
      return relativePath;
    }

    return null;
  }

  /**
   * Check script/project root directory
   */
  checkScriptDirectory() {
    const flipsPath = path.join(this.projectRoot, this.executableName);
    
    if (fs.existsSync(flipsPath)) {
      return flipsPath;
    }

    return null;
  }

  /**
   * Check common installation directories (platform-specific)
   */
  checkCommonDirectories() {
    let commonPaths = [];

    if (this.isWindows) {
      // Windows common paths
      const programFiles = process.env.ProgramFiles || 'C:\\Program Files';
      const programFilesX86 = process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)';
      const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE || 'C:\\Users\\Default', 'AppData', 'Local');
      const appData = process.env.APPDATA || path.join(process.env.USERPROFILE || 'C:\\Users\\Default', 'AppData', 'Roaming');

      commonPaths = [
        path.join(programFiles, 'Flips', 'flips.exe'),
        path.join(programFilesX86, 'Flips', 'flips.exe'),
        path.join(localAppData, 'Flips', 'flips.exe'),
        path.join(appData, 'Flips', 'flips.exe'),
        path.join(programFiles, 'flips.exe'),
        path.join(programFilesX86, 'flips.exe'),
        'C:\\flips\\flips.exe',
        'C:\\tools\\flips.exe',
      ];

    } else {
      // Unix-like systems (Linux, macOS, etc.)
      const homeDir = process.env.HOME || '/root';

      commonPaths = [
        '/usr/local/bin/flips',
        '/usr/bin/flips',
        '/opt/flips/flips',
        '/opt/local/bin/flips',
        path.join(homeDir, 'bin', 'flips'),
        path.join(homeDir, '.local', 'bin', 'flips'),
        '/snap/bin/flips',
      ];
    }

    for (const checkPath of commonPaths) {
      if (fs.existsSync(checkPath)) {
        return checkPath;
      }
    }

    return null;
  }

  /**
   * Check system PATH by attempting to execute which/where
   */
  checkSystemPath() {
    try {
      const command = this.isWindows ? `where ${this.executableName}` : `which ${this.executableName}`;
      const result = execSync(command, { 
        stdio: 'pipe',
        encoding: 'utf8',
        timeout: 5000
      }).trim();

      if (result) {
        // On Windows, 'where' might return multiple paths, take the first one
        const paths = result.split('\n').map(p => p.trim()).filter(p => p);
        if (paths.length > 0) {
          return paths[0];
        }
      }
    } catch (error) {
      // Command failed, flips not in PATH
    }

    return null;
  }

  /**
   * Validate that a path points to a valid flips binary
   */
  validateFlipsBinary(flipsPath) {
    // Check if file exists
    if (!fs.existsSync(flipsPath)) {
      return false;
    }

    // Check if it's a file (not a directory)
    const stats = fs.statSync(flipsPath);
    if (!stats.isFile()) {
      return false;
    }

    // On Unix-like systems, check if executable
    if (!this.isWindows) {
      try {
        fs.accessSync(flipsPath, fs.constants.X_OK);
      } catch (error) {
        return false;
      }
    }

    // Try to run flips with --version or --help to verify it's actually flips
    try {
      // Use a short timeout to avoid hanging
      execSync(`"${flipsPath}" --version`, { 
        stdio: 'pipe',
        timeout: 3000,
        windowsHide: true
      });
      return true;
    } catch (error) {
      // Some versions might not support --version, try --help
      try {
        execSync(`"${flipsPath}" --help`, { 
          stdio: 'pipe',
          timeout: 3000,
          windowsHide: true
        });
        return true;
      } catch (error2) {
        // If both fail, still consider it valid if it exists and has right name
        // (It might just need different flags)
        return path.basename(flipsPath).toLowerCase().includes('flips');
      }
    }
  }

  /**
   * Get flips path or throw error with helpful message
   */
  getFlipsPathOrThrow() {
    const flipsPath = this.findFlips();
    
    if (!flipsPath) {
      const errorMsg = this.generateErrorMessage();
      throw new Error(errorMsg);
    }

    return flipsPath;
  }

  /**
   * Generate helpful error message
   */
  generateErrorMessage() {
    let msg = 'Flips utility not found.\n\n';
    msg += 'Flips was searched for in the following locations:\n';
    msg += '  1. Database setting (electron/clientdata.db -> csettings table)\n';
    msg += '  2. Environment variable: FLIPS_BIN_PATH\n';
    msg += '  3. Current working directory\n';
    msg += '  4. Project root directory\n';
    msg += '  5. Common installation directories\n';
    msg += '  6. System PATH\n\n';
    msg += 'To fix this issue:\n';
    msg += '  • Download Flips from: https://github.com/Alcaro/Flips\n';
    
    if (this.isWindows) {
      msg += '  • Place flips.exe in the project root directory, OR\n';
      msg += '  • Add to PATH, OR\n';
      msg += '  • Set FLIPS_BIN_PATH environment variable, OR\n';
      msg += '  • Add to database: INSERT INTO csettings (csettinguid, csetting_name, csetting_value) VALUES (lower(hex(randomblob(16))), \'flips_path\', \'C:\\path\\to\\flips.exe\');\n';
    } else {
      msg += '  • Place flips in the project root directory, OR\n';
      msg += '  • Install to system: sudo cp flips /usr/local/bin/\n';
      msg += '  • Add to PATH, OR\n';
      msg += '  • Set FLIPS_BIN_PATH environment variable, OR\n';
      msg += '  • Add to database: INSERT INTO csettings (csettinguid, csetting_name, csetting_value) VALUES (lower(hex(randomblob(16))), \'flips_path\', \'/path/to/flips\');\n';
    }

    return msg;
  }
}

/**
 * Convenience function to get flips path
 * @param {Object} options - Options for FlipsFinder
 * @returns {string} - Path to flips binary
 * @throws {Error} - If flips not found
 */
function getFlipsPath(options = {}) {
  const finder = new FlipsFinder(options);
  return finder.getFlipsPathOrThrow();
}

/**
 * Convenience function to find flips without throwing
 * @param {Object} options - Options for FlipsFinder
 * @returns {string|null} - Path to flips binary or null
 */
function findFlips(options = {}) {
  const finder = new FlipsFinder(options);
  return finder.findFlips();
}

module.exports = {
  FlipsFinder,
  getFlipsPath,
  findFlips
};

