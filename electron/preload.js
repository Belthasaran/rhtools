const { contextBridge, ipcRenderer } = require('electron');

// Expose version info
contextBridge.exposeInMainWorld('rhtools', {
    version: '0.1.0'
});

/**
 * Expose electronAPI to renderer process
 * Provides type-safe database access via IPC
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // =============================
  // Game Data Operations
  // =============================
  
  /**
   * Get all games (latest versions only) with user annotations
   * @returns {Promise<Array>} Array of games
   */
  getGames: () => ipcRenderer.invoke('db:rhdata:get:games'),
  
  /**
   * Get all available versions for a specific game
   * @param {string} gameid - Game ID
   * @returns {Promise<Array<number>>} Array of version numbers
   */
  getVersions: (gameid) => ipcRenderer.invoke('db:rhdata:get:versions', { gameid }),
  
  /**
   * Get specific game version with annotations
   * @param {string} gameid - Game ID
   * @param {number} version - Version number
   * @returns {Promise<Object|null>} Game data or null
   */
  getGame: (gameid, version) => ipcRenderer.invoke('db:rhdata:get:game', { gameid, version }),
  
  // =============================
  // User Annotations
  // =============================
  
  /**
   * Save game annotation (game-wide)
   * @param {Object} annotation - Annotation data
   * @returns {Promise<{success: boolean}>}
   */
  saveAnnotation: (annotation) => ipcRenderer.invoke('db:clientdata:set:annotation', annotation),
  
  /**
   * Save version-specific annotation
   * @param {Object} annotation - Version-specific annotation
   * @returns {Promise<{success: boolean}>}
   */
  saveVersionAnnotation: (annotation) => ipcRenderer.invoke('db:clientdata:set:version-annotation', annotation),
  
  // =============================
  // Stage Operations
  // =============================
  
  /**
   * Get stages for a game with user annotations
   * @param {string} gameid - Game ID
   * @returns {Promise<Array>} Array of stages
   */
  getStages: (gameid) => ipcRenderer.invoke('db:clientdata:get:stages', { gameid }),
  
  /**
   * Save stage annotation
   * @param {Object} annotation - Stage annotation
   * @returns {Promise<{success: boolean}>}
   */
  saveStageAnnotation: (annotation) => ipcRenderer.invoke('db:clientdata:set:stage-annotation', annotation),
  
  /**
   * Save multiple stage annotations at once
   * @param {Array} annotations - Array of stage annotations
   * @returns {Promise<{success: boolean}>}
   */
  saveStageAnnotationsBulk: (annotations) => ipcRenderer.invoke('db:clientdata:set:stage-annotations-bulk', { annotations }),
  
  // =============================
  // Settings Operations
  // =============================
  
  /**
   * Get all settings
   * @returns {Promise<Object>} Settings object
   */
  getSettings: () => ipcRenderer.invoke('db:settings:get:all'),
  
  /**
   * Set a single setting
   * @param {string} name - Setting name
   * @param {string} value - Setting value
   * @returns {Promise<{success: boolean}>}
   */
  setSetting: (name, value) => ipcRenderer.invoke('db:settings:set:value', { name, value }),
  
  /**
   * Save multiple settings at once
   * @param {Object} settings - Settings object
   * @returns {Promise<{success: boolean}>}
   */
  saveSettings: (settings) => ipcRenderer.invoke('db:settings:set:bulk', { settings }),
  
  // =============================
  // Run System Operations
  // =============================
  
  /**
   * Create a new run
   * @param {string} runName - Run name
   * @param {string} runDescription - Run description
   * @param {Array} globalConditions - Global challenge conditions
   * @returns {Promise<{success: boolean, runUuid: string}>}
   */
  createRun: (runName, runDescription, globalConditions) => 
    ipcRenderer.invoke('db:runs:create', { runName, runDescription, globalConditions }),
  
  /**
   * Save run plan entries
   * @param {string} runUuid - Run UUID
   * @param {Array} entries - Run plan entries
   * @returns {Promise<{success: boolean}>}
   */
  saveRunPlan: (runUuid, entries) => ipcRenderer.invoke('db:runs:save-plan', { runUuid, entries }),
  
  /**
   * Start a run (change status to active, expand plan to results)
   * @param {Object} params - {runUuid: string}
   * @returns {Promise<{success: boolean}>}
   */
  startRun: (params) => ipcRenderer.invoke('db:runs:start', params),
  
  /**
   * Record challenge result
   * @param {Object} params - {runUuid: string, challengeIndex: number, status: string}
   * @returns {Promise<{success: boolean}>}
   */
  recordChallengeResult: (params) => ipcRenderer.invoke('db:runs:record-result', params),
  
  /**
   * Cancel a run
   * @param {Object} params - {runUuid: string}
   * @returns {Promise<{success: boolean}>}
   */
  cancelRun: (params) => ipcRenderer.invoke('db:runs:cancel', params),
  
  /**
   * Get run results (expanded challenges)
   * @param {Object} params - {runUuid: string}
   * @returns {Promise<Array>} Array of run results
   */
  getRunResults: (params) => ipcRenderer.invoke('db:runs:get-results', params),
  
  /**
   * Reveal a random challenge (select game and update)
   * @param {Object} params - {runUuid: string, resultUuid: string, revealedEarly: boolean}
   * @returns {Promise<{success: boolean, gameid?: string, gameName?: string}>}
   */
  revealChallenge: (params) => ipcRenderer.invoke('db:runs:reveal-challenge', params),
  
  /**
   * Mark a challenge as revealed early (after using Back button)
   * @param {Object} params - {runUuid: string, challengeIndex: number, revealedEarly: boolean}
   * @returns {Promise<{success: boolean}>}
   */
  markChallengeRevealedEarly: (params) => ipcRenderer.invoke('db:runs:mark-revealed-early', params),
  
  /**
   * Get active run (for startup check)
   * @returns {Promise<Object|null>} Active run with calculated elapsed time
   */
  getActiveRun: () => ipcRenderer.invoke('db:runs:get-active'),
  
  /**
   * Pause a run
   * @param {string} runUuid - Run UUID
   * @returns {Promise<{success: boolean}>}
   */
  pauseRun: (runUuid) => ipcRenderer.invoke('db:runs:pause', { runUuid }),
  
  /**
   * Unpause a run
   * @param {string} runUuid - Run UUID
   * @returns {Promise<{success: boolean}>}
   */
  unpauseRun: (runUuid) => ipcRenderer.invoke('db:runs:unpause', { runUuid }),
  
  /**
   * Expand run plan and select all random games
   * @param {Object} params - {runUuid}
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  expandAndStageRun: (params) => ipcRenderer.invoke('db:runs:expand-and-prepare', params),
  
  /**
   * Stage run games (create SFC files)
   * @param {Object} params - {runUuid, expandedResults, vanillaRomPath, flipsPath}
   * @returns {Promise<{success: boolean, stagingFolder?: string, error?: string}>}
   */
  stageRunGames: (params) => ipcRenderer.invoke('db:runs:stage-games', params),
  
  // =============================
  // Seed Management
  // =============================
  
  /**
   * Generate a new random seed
   * @returns {Promise<{success: boolean, seed: string, mapId: string, gameCount: number}>}
   */
  generateSeed: () => ipcRenderer.invoke('db:seeds:generate'),
  
  /**
   * Get all available seed mappings
   * @returns {Promise<Array>} Array of seed mappings
   */
  getSeedMappings: () => ipcRenderer.invoke('db:seeds:get-mappings'),
  
  /**
   * Validate a seed
   * @param {string} seed - Seed to validate
   * @returns {Promise<{valid: boolean, mapId?: string, gameCount?: number}>}
   */
  validateSeed: (seed) => ipcRenderer.invoke('db:seeds:validate', { seed }),
  
  /**
   * Export run with seed mappings
   * @param {string} runUuid - Run UUID
   * @returns {Promise<{success: boolean, data?: Object}>}
   */
  exportRun: (runUuid) => ipcRenderer.invoke('db:runs:export', { runUuid }),
  
  /**
   * Import run with seed mappings
   * @param {Object} importData - Import data
   * @returns {Promise<{success: boolean, runUuid?: string, warnings?: Array}>}
   */
  importRun: (importData) => ipcRenderer.invoke('db:runs:import', { importData }),
  
  /**
   * Access to ipcRenderer for event listeners
   */
  ipcRenderer: {
    on: (channel, func) => ipcRenderer.on(channel, func),
    removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
  },
  
  /**
   * Shell operations for opening folders/files
   */
  shell: {
    openPath: (path) => ipcRenderer.invoke('shell:open-path', path)
  }
});
