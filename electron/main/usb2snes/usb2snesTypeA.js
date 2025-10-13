/**
 * usb2snesTypeA - Type A implementation (Python py2snes port)
 * 
 * This is a JavaScript port of the py2snes Python library.
 * It implements the USB2SNES WebSocket protocol to communicate with
 * USB2SNES/QUsb2snes servers.
 * 
 * Based on: py2snes/__init__.py from the project's Python codebase
 * 
 * Protocol Reference:
 * - https://github.com/Skarsnik/QUsb2snes/blob/master/docs/Protocol.md
 * - Default WebSocket address: ws://localhost:64213
 */

const { 
  BaseUsb2snes, 
  SNES_DISCONNECTED, 
  SNES_CONNECTING, 
  SNES_CONNECTED, 
  SNES_ATTACHED,
  ROM_START,
  WRAM_START,
  WRAM_SIZE,
  SRAM_START
} = require('./BaseUsb2snes');

// WebSocket library - using 'ws' package
const WebSocket = require('ws');

class Usb2snesTypeA extends BaseUsb2snes {
  constructor() {
    super();
    this.socket = null;
    this.recvQueue = [];
    this.requestLock = false;
    this.recvTask = null;
  }

  /**
   * Connect to USB2SNES WebSocket server
   * @param {string} address - WebSocket address (e.g., 'ws://localhost:64213')
   * @returns {Promise<void>}
   */
  async connect(address = 'ws://localhost:64213') {
    if (this.socket !== null) {
      console.log('[usb2snesTypeA] Already connected');
      return;
    }

    this.state = SNES_CONNECTING;

    console.log(`[usb2snesTypeA] Connecting to ${address}...`);

    try {
      // Create WebSocket connection
      this.socket = new WebSocket(address, {
        // Disable automatic ping/pong to match Python implementation
        perMessageDeflate: false
      });

      // Set up event handlers
      await this._setupWebSocket();

      this.state = SNES_CONNECTED;
      console.log('[usb2snesTypeA] Connected successfully');
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    }
  }

  /**
   * Set up WebSocket event handlers
   * @private
   */
  async _setupWebSocket() {
    return new Promise((resolve, reject) => {
      this.socket.on('open', () => {
        console.log('[usb2snesTypeA] WebSocket opened');
        // Start receive loop
        this._startRecvLoop();
        resolve();
      });

      this.socket.on('error', (error) => {
        console.error('[usb2snesTypeA] WebSocket error:', error);
        reject(error);
      });

      this.socket.on('close', () => {
        console.log('[usb2snesTypeA] WebSocket closed');
        this.socket = null;
        this.state = SNES_DISCONNECTED;
        this.recvQueue = [];
      });
    });
  }

  /**
   * Start receiving loop to queue incoming messages
   * @private
   */
  _startRecvLoop() {
    this.socket.on('message', (data) => {
      // Queue incoming data
      this.recvQueue.push(data);
    });
  }

  /**
   * Disconnect from USB2SNES server
   * @returns {Promise<void>}
   */
  async disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.state = SNES_DISCONNECTED;
    this.recvQueue = [];
    this.device = null;
    this.isSD2SNES = false;
  }

  /**
   * Get list of available devices
   * @returns {Promise<string[]>} Array of device names
   */
  async DeviceList() {
    // Wait for request lock
    while (this.requestLock) {
      await this._sleep(10);
    }
    this.requestLock = true;

    try {
      if (this.state < SNES_CONNECTED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return null;
      }

      const request = {
        Opcode: "DeviceList",
        Space: "SNES"
      };

      this.socket.send(JSON.stringify(request));

      // Wait for response with timeout
      const reply = await this._waitForResponse(5000);
      const devices = reply.Results && reply.Results.length > 0 ? reply.Results : null;

      if (!devices) {
        throw new Error('No devices found');
      }

      return devices;
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    } finally {
      this.requestLock = false;
    }
  }

  /**
   * Attach to a specific device
   * @param {string} device - Device name from DeviceList
   * @returns {Promise<void>}
   */
  async Attach(device) {
    if (this.state !== SNES_CONNECTED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('Not connected to USB2SNES server');
    }

    try {
      const request = {
        Opcode: "Attach",
        Space: "SNES",
        Operands: [device]
      };

      this.socket.send(JSON.stringify(request));
      this.state = SNES_ATTACHED;

      // Detect if SD2SNES device
      if (device.toLowerCase().includes('sd2snes') || (device.length === 4 && device.substring(0, 3) === 'COM')) {
        this.isSD2SNES = true;
      } else {
        this.isSD2SNES = false;
      }

      this.device = device;
      console.log(`[usb2snesTypeA] Attached to ${device}, isSD2SNES: ${this.isSD2SNES}`);
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    }
  }

  /**
   * Get device information
   * @returns {Promise<Object>} Device info
   */
  async Info() {
    while (this.requestLock) {
      await this._sleep(10);
    }
    this.requestLock = true;

    try {
      if (this.state !== SNES_ATTACHED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return null;
      }

      const request = {
        Opcode: "Info",
        Space: "SNES",
        Operands: [this.device]
      };

      this.socket.send(JSON.stringify(request));

      const reply = await this._waitForResponse(5000);
      const info = reply.Results && reply.Results.length > 0 ? reply.Results : [];

      return {
        firmwareversion: this._listItem(info, 0),
        versionstring: this._listItem(info, 1),
        romrunning: this._listItem(info, 2),
        flag1: this._listItem(info, 3),
        flag2: this._listItem(info, 4)
      };
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    } finally {
      this.requestLock = false;
    }
  }

  /**
   * Set client name
   * @param {string} name - Client identifier
   * @returns {Promise<void>}
   */
  async Name(name) {
    if (this.state !== SNES_ATTACHED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }

    try {
      const request = {
        Opcode: "Name",
        Space: "SNES",
        Operands: [name]
      };

      this.socket.send(JSON.stringify(request));
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    }
  }

  /**
   * Boot a ROM file
   * @param {string} romPath - Path to ROM on console
   * @returns {Promise<void>}
   */
  async Boot(romPath) {
    if (this.state !== SNES_ATTACHED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('Not attached to device');
    }

    try {
      const request = {
        Opcode: "Boot",
        Space: "SNES",
        Operands: [romPath]
      };

      this.socket.send(JSON.stringify(request));
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    }
  }

  /**
   * Return to menu
   * @returns {Promise<void>}
   */
  async Menu() {
    if (this.state !== SNES_ATTACHED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('Not attached to device');
    }

    try {
      const request = {
        Opcode: "Menu",
        Space: "SNES"
      };

      console.log('[usb2snesTypeA] Sending Menu command:', JSON.stringify(request));
      this.socket.send(JSON.stringify(request));
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    }
  }

  /**
   * Reset console
   * @returns {Promise<void>}
   */
  async Reset() {
    if (this.state !== SNES_ATTACHED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('Not attached to device');
    }

    try {
      const request = {
        Opcode: "Reset",
        Space: "SNES"
      };

      this.socket.send(JSON.stringify(request));
    } catch (error) {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.state = SNES_DISCONNECTED;
      throw error;
    }
  }

  /**
   * Read memory from console
   * @param {number} address - Memory address
   * @param {number} size - Number of bytes
   * @returns {Promise<Buffer>} Data read
   */
  async GetAddress(address, size) {
    while (this.requestLock) {
      await this._sleep(10);
    }
    this.requestLock = true;

    try {
      if (this.state !== SNES_ATTACHED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return null;
      }

      const request = {
        Opcode: "GetAddress",
        Space: "SNES",
        Operands: [address.toString(16), size.toString(16)]
      };

      this.socket.send(JSON.stringify(request));

      // Read binary data
      let data = Buffer.alloc(0);
      while (data.length < size) {
        const chunk = await this._waitForBinaryResponse(5000);
        if (!chunk) break;
        data = Buffer.concat([data, chunk]);
      }

      if (data.length !== size) {
        console.error(`[usb2snesTypeA] Error reading ${address.toString(16)}, requested ${size} bytes, received ${data.length}`);
        if (this.socket) {
          this.socket.close();
        }
        return null;
      }

      return data;
    } finally {
      this.requestLock = false;
    }
  }

  /**
   * Write memory to console
   * NOTE: Full implementation with SD2SNES special handling to be added
   * @param {Array<[number, Buffer]>} writeList - Array of [address, data] tuples
   * @returns {Promise<boolean>} Success status
   */
  async PutAddress(writeList) {
    while (this.requestLock) {
      await this._sleep(10);
    }
    this.requestLock = true;

    try {
      if (this.state !== SNES_ATTACHED || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return false;
      }

      const request = {
        Opcode: "PutAddress",
        Operands: []
      };

      if (this.isSD2SNES) {
        // TODO: Implement SD2SNES special handling (CMD space with assembly)
        // See py2snes lines 257-280
        throw new Error('SD2SNES PutAddress not yet implemented');
      } else {
        request.Space = 'SNES';
        
        for (const [address, data] of writeList) {
          request.Operands = [address.toString(16), data.length.toString(16)];
          this.socket.send(JSON.stringify(request));
          this.socket.send(data);
        }
      }

      return true;
    } catch (error) {
      console.error('[usb2snesTypeA] PutAddress error:', error);
      return false;
    } finally {
      this.requestLock = false;
    }
  }

  /**
   * Upload file to console
   * NOTE: Basic implementation - optimizations to be added
   * @param {string} srcFile - Source file path
   * @param {string} dstFile - Destination file path
   * @returns {Promise<boolean>} Success status
   */
  async PutFile(srcFile, dstFile) {
    // TODO: Implement file upload
    // See py2snes lines 334-368
    throw new Error('PutFile not yet implemented');
  }

  /**
   * List directory contents
   * NOTE: Basic implementation to be added
   * @param {string} dirPath - Directory path
   * @returns {Promise<Array>} Directory listing
   */
  async List(dirPath) {
    // TODO: Implement directory listing
    // See py2snes lines 385-448
    throw new Error('List not yet implemented');
  }

  /**
   * Create directory
   * @param {string} dirPath - Directory path
   * @returns {Promise<void>}
   */
  async MakeDir(dirPath) {
    // TODO: Implement MakeDir
    // See py2snes lines 450-480
    throw new Error('MakeDir not yet implemented');
  }

  /**
   * Remove file/directory
   * @param {string} path - Path to remove
   * @returns {Promise<void>}
   */
  async Remove(path) {
    // TODO: Implement Remove
    // See py2snes lines 482-500
    throw new Error('Remove not yet implemented');
  }

  // ========================================
  // Helper Methods
  // ========================================

  /**
   * Wait for JSON response with timeout
   * @private
   */
  async _waitForResponse(timeout) {
    const startTime = Date.now();
    while (this.recvQueue.length === 0) {
      if (Date.now() - startTime > timeout) {
        throw new Error('Response timeout');
      }
      await this._sleep(10);
    }
    const msg = this.recvQueue.shift();
    return JSON.parse(msg.toString());
  }

  /**
   * Wait for binary response with timeout
   * @private
   */
  async _waitForBinaryResponse(timeout) {
    const startTime = Date.now();
    while (this.recvQueue.length === 0) {
      if (Date.now() - startTime > timeout) {
        return null;
      }
      await this._sleep(10);
    }
    const msg = this.recvQueue.shift();
    return Buffer.isBuffer(msg) ? msg : Buffer.from(msg);
  }

  /**
   * Get list item safely
   * @private
   */
  _listItem(list, index) {
    try {
      return list[index] || null;
    } catch {
      return null;
    }
  }

  /**
   * Sleep helper
   * @private
   */
  async _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = Usb2snesTypeA;

