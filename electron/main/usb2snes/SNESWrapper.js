/**
 * SNESWrapper - Unified interface for all USB2SNES implementations
 * 
 * This is the ONLY module that other parts of the application should use
 * to communicate with USB2SNES. It acts as a facade/broker that delegates
 * calls to the currently selected implementation (usb2snes_a, usb2snes_b, etc.).
 * 
 * Benefits:
 * - Single point of interface for all USB2SNES operations
 * - Easy switching between implementations
 * - Consistent API regardless of underlying implementation
 * - Centralized error handling and logging
 * 
 * Usage:
 *   const snesWrapper = new SNESWrapper();
 *   await snesWrapper.setImplementation('usb2snes_a');
 *   await snesWrapper.connect('ws://localhost:64213');
 *   const devices = await snesWrapper.DeviceList();
 */

const { SNES_DISCONNECTED, SNES_CONNECTING, SNES_CONNECTED, SNES_ATTACHED } = require('./BaseUsb2snes');

class SNESWrapper {
  constructor() {
    this.currentImplementation = null;
    this.implementationType = null;
    this.implementationInstance = null;
  }

  /**
   * Set the USB2SNES implementation to use
   * @param {string} implementation - One of: 'usb2snes_a', 'usb2snes_b', 'qusb2snes', 'node-usb'
   * @returns {Promise<void>}
   * @throws {Error} If implementation is not recognized or cannot be loaded
   */
  async setImplementation(implementation) {
    // Cannot change implementation while connected
    if (this.implementationInstance && this.implementationInstance.isConnected()) {
      throw new Error('Cannot change USB2SNES implementation while connected. Disconnect first.');
    }

    // Validate implementation type
    const validImplementations = ['usb2snes_a', 'usb2snes_b', 'qusb2snes', 'node-usb'];
    if (!validImplementations.includes(implementation)) {
      throw new Error(`Invalid implementation: ${implementation}. Must be one of: ${validImplementations.join(', ')}`);
    }

    // Clear existing instance
    this.implementationInstance = null;
    this.implementationType = null;

    // Load the implementation module
    try {
      let ImplementationClass;
      
      switch (implementation) {
        case 'usb2snes_a':
          ImplementationClass = require('./usb2snesTypeA');
          break;
        case 'usb2snes_b':
          ImplementationClass = require('./usb2snesTypeB');
          break;
        case 'qusb2snes':
          ImplementationClass = require('./qusb2snesAdapter');
          break;
        case 'node-usb':
          ImplementationClass = require('./nodeUsbAdapter');
          break;
        default:
          throw new Error(`Implementation ${implementation} not found`);
      }

      // Create instance
      this.implementationInstance = new ImplementationClass();
      this.implementationType = implementation;
      
      console.log(`[SNESWrapper] Set implementation to: ${implementation}`);
    } catch (error) {
      // Check if it's a "not implemented" error (module doesn't exist yet)
      if (error.code === 'MODULE_NOT_FOUND') {
        throw new Error(`Implementation '${implementation}' is not yet implemented. Only usb2snes_a is currently available.`);
      }
      throw error;
    }
  }

  /**
   * Get the current implementation type
   * @returns {string|null} Current implementation name or null if none set
   */
  getImplementationType() {
    return this.implementationType;
  }

  /**
   * Check if an implementation is currently loaded
   * @returns {boolean}
   */
  hasImplementation() {
    return this.implementationInstance !== null;
  }

  /**
   * Ensure implementation is loaded
   * @private
   * @throws {Error} If no implementation is set
   */
  _ensureImplementation() {
    if (!this.implementationInstance) {
      throw new Error('No USB2SNES implementation loaded. Call setImplementation() first.');
    }
  }

  // ========================================
  // Connection Management
  // ========================================

  /**
   * Connect to USB2SNES server/device
   * @param {string} address - WebSocket address (default: 'ws://localhost:64213')
   * @returns {Promise<void>}
   */
  async connect(address = 'ws://localhost:64213') {
    this._ensureImplementation();
    console.log(`[SNESWrapper] Connecting to ${address} using ${this.implementationType}`);
    return await this.implementationInstance.connect(address);
  }

  /**
   * Disconnect from USB2SNES server/device
   * @returns {Promise<void>}
   */
  async disconnect() {
    this._ensureImplementation();
    console.log(`[SNESWrapper] Disconnecting from USB2SNES`);
    return await this.implementationInstance.disconnect();
  }

  // ========================================
  // Device Operations
  // ========================================

  /**
   * Get list of available devices
   * @returns {Promise<string[]>} Array of device names
   */
  async DeviceList() {
    this._ensureImplementation();
    return await this.implementationInstance.DeviceList();
  }

  /**
   * Attach to a specific device
   * @param {string} device - Device name from DeviceList
   * @returns {Promise<void>}
   */
  async Attach(device) {
    this._ensureImplementation();
    console.log(`[SNESWrapper] Attaching to device: ${device}`);
    return await this.implementationInstance.Attach(device);
  }

  /**
   * Get device information
   * @returns {Promise<Object>} Device info
   */
  async Info() {
    this._ensureImplementation();
    return await this.implementationInstance.Info();
  }

  /**
   * Set client name for this connection
   * @param {string} name - Client identifier
   * @returns {Promise<void>}
   */
  async Name(name) {
    this._ensureImplementation();
    return await this.implementationInstance.Name(name);
  }

  // ========================================
  // Console Control
  // ========================================

  /**
   * Boot a ROM file on the console
   * @param {string} romPath - Path to ROM on console
   * @returns {Promise<void>}
   */
  async Boot(romPath) {
    this._ensureImplementation();
    console.log(`[SNESWrapper] Booting ROM: ${romPath}`);
    return await this.implementationInstance.Boot(romPath);
  }

  /**
   * Return console to menu
   * @returns {Promise<void>}
   */
  async Menu() {
    this._ensureImplementation();
    console.log(`[SNESWrapper] Returning to menu`);
    return await this.implementationInstance.Menu();
  }

  /**
   * Reset the console
   * @returns {Promise<void>}
   */
  async Reset() {
    this._ensureImplementation();
    console.log(`[SNESWrapper] Resetting console`);
    return await this.implementationInstance.Reset();
  }

  // ========================================
  // Memory Operations
  // ========================================

  /**
   * Read memory from console
   * @param {number} address - Memory address
   * @param {number} size - Number of bytes to read
   * @returns {Promise<Buffer>} Data read
   */
  async GetAddress(address, size) {
    this._ensureImplementation();
    return await this.implementationInstance.GetAddress(address, size);
  }

  /**
   * Write memory to console
   * @param {Array<[number, Buffer]>} writeList - Array of [address, data] tuples
   * @returns {Promise<boolean>} Success status
   */
  async PutAddress(writeList) {
    this._ensureImplementation();
    return await this.implementationInstance.PutAddress(writeList);
  }

  // ========================================
  // File Operations
  // ========================================

  /**
   * Upload a file to the console
   * @param {string} srcFile - Source file path (local)
   * @param {string} dstFile - Destination file path (on console)
   * @returns {Promise<boolean>} Success status
   */
  async PutFile(srcFile, dstFile) {
    this._ensureImplementation();
    console.log(`[SNESWrapper] Uploading file: ${srcFile} -> ${dstFile}`);
    return await this.implementationInstance.PutFile(srcFile, dstFile);
  }

  /**
   * List directory contents on console
   * @param {string} dirPath - Directory path
   * @returns {Promise<Array<{type: string, filename: string}>>} Directory listing
   */
  async List(dirPath) {
    this._ensureImplementation();
    return await this.implementationInstance.List(dirPath);
  }

  /**
   * Create directory on console
   * @param {string} dirPath - Directory path to create
   * @returns {Promise<void>}
   */
  async MakeDir(dirPath) {
    this._ensureImplementation();
    return await this.implementationInstance.MakeDir(dirPath);
  }

  /**
   * Remove file or directory on console
   * @param {string} path - Path to remove
   * @returns {Promise<void>}
   */
  async Remove(path) {
    this._ensureImplementation();
    return await this.implementationInstance.Remove(path);
  }

  // ========================================
  // State Queries
  // ========================================

  /**
   * Get current connection state
   * @returns {number} State constant
   */
  getState() {
    if (!this.implementationInstance) return SNES_DISCONNECTED;
    return this.implementationInstance.getState();
  }

  /**
   * Check if connected
   * @returns {boolean}
   */
  isConnected() {
    if (!this.implementationInstance) return false;
    return this.implementationInstance.isConnected();
  }

  /**
   * Check if attached to a device
   * @returns {boolean}
   */
  isAttached() {
    if (!this.implementationInstance) return false;
    return this.implementationInstance.isAttached();
  }

  /**
   * Get connected device name
   * @returns {string|null}
   */
  getDevice() {
    if (!this.implementationInstance) return null;
    return this.implementationInstance.getDevice();
  }

  // ========================================
  // Convenience Methods
  // ========================================

  /**
   * Quick connect: Set implementation and connect in one call
   * @param {string} implementation - Implementation type
   * @param {string} address - WebSocket address
   * @returns {Promise<void>}
   */
  async quickConnect(implementation, address = 'ws://localhost:64213') {
    await this.setImplementation(implementation);
    await this.connect(address);
  }

  /**
   * Full connect flow: Connect, get devices, attach to first device
   * @param {string} implementation - Implementation type
   * @param {string} address - WebSocket address
   * @param {string|null} deviceName - Specific device to attach to, or null for first device
   * @returns {Promise<Object>} Connection info (device, info)
   */
  async fullConnect(implementation, address = 'ws://localhost:64213', deviceName = null) {
    await this.setImplementation(implementation);
    await this.connect(address);
    
    const devices = await this.DeviceList();
    if (!devices || devices.length === 0) {
      throw new Error('No devices found');
    }
    
    const device = deviceName || devices[0];
    await this.Attach(device);
    
    const info = await this.Info();
    
    return {
      device,
      devices,
      info
    };
  }
}

// Export wrapper class and constants
module.exports = {
  SNESWrapper,
  // Re-export constants for convenience
  SNES_DISCONNECTED,
  SNES_CONNECTING,
  SNES_CONNECTED,
  SNES_ATTACHED
};

