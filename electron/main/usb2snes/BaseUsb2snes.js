/**
 * BaseUsb2snes - Abstract base class/interface for all USB2SNES implementations
 * 
 * All concrete USB2SNES library implementations must extend this class
 * and implement all methods. This ensures a consistent interface across
 * all implementations (usb2snes_a, usb2snes_b, qusb2snes, node-usb).
 * 
 * @abstract
 */

// Connection states (shared across all implementations)
const SNES_DISCONNECTED = 0;
const SNES_CONNECTING = 1;
const SNES_CONNECTED = 2;
const SNES_ATTACHED = 3;

// Memory address spaces (SNES memory map)
const ROM_START = 0x000000;
const WRAM_START = 0xF50000;
const WRAM_SIZE = 0x20000;
const SRAM_START = 0xE00000;

class BaseUsb2snes {
  constructor() {
    if (new.target === BaseUsb2snes) {
      throw new TypeError("Cannot construct BaseUsb2snes instances directly - must extend this class");
    }
    
    this.state = SNES_DISCONNECTED;
    this.device = null;
    this.isSD2SNES = false;
  }

  /**
   * Connect to USB2SNES server/device
   * @param {string} address - WebSocket address (e.g., 'ws://localhost:64213')
   * @returns {Promise<void>}
   */
  async connect(address) {
    throw new Error("connect() must be implemented by subclass");
  }

  /**
   * Disconnect from USB2SNES server/device
   * @returns {Promise<void>}
   */
  async disconnect() {
    throw new Error("disconnect() must be implemented by subclass");
  }

  /**
   * Get list of available devices
   * @returns {Promise<string[]>} Array of device names
   */
  async DeviceList() {
    throw new Error("DeviceList() must be implemented by subclass");
  }

  /**
   * Attach to a specific device
   * @param {string} device - Device name from DeviceList
   * @returns {Promise<void>}
   */
  async Attach(device) {
    throw new Error("Attach() must be implemented by subclass");
  }

  /**
   * Get device information (firmware, version, ROM running, etc.)
   * @returns {Promise<Object>} Device info object
   * @returns {string} return.firmwareversion - Firmware version
   * @returns {string} return.versionstring - Version string
   * @returns {string} return.romrunning - Currently running ROM
   * @returns {string} return.flag1 - Device flag 1
   * @returns {string} return.flag2 - Device flag 2
   */
  async Info() {
    throw new Error("Info() must be implemented by subclass");
  }

  /**
   * Set client name for this connection
   * @param {string} name - Client identifier name
   * @returns {Promise<void>}
   */
  async Name(name) {
    throw new Error("Name() must be implemented by subclass");
  }

  /**
   * Boot a ROM file on the console
   * @param {string} romPath - Path to ROM file on console/SD card
   * @returns {Promise<void>}
   */
  async Boot(romPath) {
    throw new Error("Boot() must be implemented by subclass");
  }

  /**
   * Return console to menu
   * @returns {Promise<void>}
   */
  async Menu() {
    throw new Error("Menu() must be implemented by subclass");
  }

  /**
   * Reset the console
   * @returns {Promise<void>}
   */
  async Reset() {
    throw new Error("Reset() must be implemented by subclass");
  }

  /**
   * Read memory from console
   * @param {number} address - Memory address to read from
   * @param {number} size - Number of bytes to read
   * @returns {Promise<Buffer>} Data read from memory
   */
  async GetAddress(address, size) {
    throw new Error("GetAddress() must be implemented by subclass");
  }

  /**
   * Write memory to console
   * @param {Array<[number, Buffer]>} writeList - Array of [address, data] tuples
   * @returns {Promise<boolean>} Success status
   */
  async PutAddress(writeList) {
    throw new Error("PutAddress() must be implemented by subclass");
  }

  /**
   * Upload a file to the console
   * @param {string} srcFile - Source file path (local)
   * @param {string} dstFile - Destination file path (on console)
   * @returns {Promise<boolean>} Success status
   */
  async PutFile(srcFile, dstFile) {
    throw new Error("PutFile() must be implemented by subclass");
  }

  /**
   * List directory contents on console
   * @param {string} dirPath - Directory path on console
   * @returns {Promise<Array<{type: string, filename: string}>>} Directory listing
   */
  async List(dirPath) {
    throw new Error("List() must be implemented by subclass");
  }

  /**
   * Create directory on console
   * @param {string} dirPath - Directory path to create
   * @returns {Promise<void>}
   */
  async MakeDir(dirPath) {
    throw new Error("MakeDir() must be implemented by subclass");
  }

  /**
   * Remove file or directory on console
   * @param {string} path - Path to remove
   * @returns {Promise<void>}
   */
  async Remove(path) {
    throw new Error("Remove() must be implemented by subclass");
  }

  /**
   * Get current connection state
   * @returns {number} State constant (SNES_DISCONNECTED, SNES_CONNECTING, SNES_CONNECTED, SNES_ATTACHED)
   */
  getState() {
    return this.state;
  }

  /**
   * Check if connected (CONNECTED or ATTACHED state)
   * @returns {boolean}
   */
  isConnected() {
    return this.state >= SNES_CONNECTED;
  }

  /**
   * Check if attached to a device
   * @returns {boolean}
   */
  isAttached() {
    return this.state === SNES_ATTACHED;
  }

  /**
   * Get connected device name
   * @returns {string|null}
   */
  getDevice() {
    return this.device;
  }
}

// Export constants and class
module.exports = {
  BaseUsb2snes,
  // Connection states
  SNES_DISCONNECTED,
  SNES_CONNECTING,
  SNES_CONNECTED,
  SNES_ATTACHED,
  // Memory spaces
  ROM_START,
  WRAM_START,
  WRAM_SIZE,
  SRAM_START
};

