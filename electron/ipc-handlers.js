/**
 * IPC Handlers for RHTools Electron App
 * 
 * Handles communication between renderer process (Vue.js) and main process (Node.js)
 * Provides database access, game data, user annotations, and settings
 */

const { ipcMain } = require('electron');
const crypto = require('crypto');

/**
 * Register all IPC handlers with the database manager
 * @param {DatabaseManager} dbManager - Database manager instance
 */
function registerDatabaseHandlers(dbManager) {
  
  // ===========================================================================
  // GAME DATA OPERATIONS (rhdata.db)
  // ===========================================================================
  
  /**
   * Get all games (latest versions only) with user annotations
   * Channel: db:rhdata:get:games
   */
  ipcMain.handle('db:rhdata:get:games', async () => {
    try {
      return dbManager.withClientData('rhdata', (db) => {
        const games = db.prepare(`
          SELECT 
            gv.gameid as Id,
            gv.name as Name,
            gv.author as Author,
            gv.length as Length,
            gv.combinedtype as Type,
            gv.legacy_type as LegacyType,
            gv.difficulty as PublicDifficulty,
            gv.version as CurrentVersion,
            gv.local_runexcluded as LocalRunExcluded,
            gv.gvjsondata as JsonData,
            COALESCE(uga.status, 'Default') as Status,
            uga.user_difficulty_rating as MyDifficultyRating,
            uga.user_review_rating as MyReviewRating,
            uga.user_skill_rating as MySkillRating,
            COALESCE(uga.hidden, 0) as Hidden,
            COALESCE(uga.exclude_from_random, 0) as ExcludeFromRandom,
            uga.user_notes as Mynotes
          FROM gameversions gv
          LEFT JOIN clientdata.user_game_annotations uga ON gv.gameid = uga.gameid
          WHERE gv.removed = 0
            AND gv.version = (
              SELECT MAX(version) FROM gameversions gv2 
              WHERE gv2.gameid = gv.gameid
            )
          ORDER BY gv.name
        `).all();
        
        // Parse JSON data and convert booleans
        return games.map(g => ({
          ...g,
          JsonData: g.JsonData ? JSON.parse(g.JsonData) : null,
          Hidden: Boolean(g.Hidden),
          ExcludeFromRandom: Boolean(g.ExcludeFromRandom),
          LocalRunExcluded: Boolean(g.LocalRunExcluded),
        }));
      });
    } catch (error) {
      console.error('Error getting games:', error);
      throw error;
    }
  });

  /**
   * Get all available versions for a specific game
   * Channel: db:rhdata:get:versions
   */
  ipcMain.handle('db:rhdata:get:versions', async (event, { gameid }) => {
    try {
      const db = dbManager.getConnection('rhdata');
      
      const versions = db.prepare(`
        SELECT DISTINCT version 
        FROM gameversions 
        WHERE gameid = ?
        ORDER BY version DESC
      `).all(gameid);
      
      return versions.map(v => v.version);
    } catch (error) {
      console.error('Error getting versions:', error);
      throw error;
    }
  });

  /**
   * Get specific game version with annotations
   * Channel: db:rhdata:get:game
   */
  ipcMain.handle('db:rhdata:get:game', async (event, { gameid, version }) => {
    try {
      return dbManager.withClientData('rhdata', (db) => {
        const game = db.prepare(`
          SELECT 
            gv.gameid as Id,
            gv.name as Name,
            gv.author as Author,
            gv.length as Length,
            gv.combinedtype as Type,
            gv.legacy_type as LegacyType,
            gv.difficulty as PublicDifficulty,
            gv.version as CurrentVersion,
            gv.gvjsondata as JsonData,
            -- Check for version-specific annotation first, fall back to game-wide
            COALESCE(ugva.status, uga.status, 'Default') as Status,
            COALESCE(ugva.user_difficulty_rating, uga.user_difficulty_rating) as MyDifficultyRating,
            COALESCE(ugva.user_review_rating, uga.user_review_rating) as MyReviewRating,
            COALESCE(ugva.user_skill_rating, uga.user_skill_rating) as MySkillRating,
            COALESCE(uga.hidden, 0) as Hidden,
            COALESCE(uga.exclude_from_random, 0) as ExcludeFromRandom,
            COALESCE(ugva.user_notes, uga.user_notes) as Mynotes,
            -- Flag if this has version-specific annotations
            CASE WHEN ugva.annotation_key IS NOT NULL THEN 1 ELSE 0 END as HasVersionSpecific
          FROM gameversions gv
          LEFT JOIN clientdata.user_game_annotations uga ON gv.gameid = uga.gameid
          LEFT JOIN clientdata.user_game_version_annotations ugva 
            ON gv.gameid = ugva.gameid AND gv.version = ugva.version
          WHERE gv.gameid = ? AND gv.version = ?
        `).get(gameid, version);
        
        if (!game) return null;
        
        return {
          ...game,
          JsonData: game.JsonData ? JSON.parse(game.JsonData) : null,
          Hidden: Boolean(game.Hidden),
          ExcludeFromRandom: Boolean(game.ExcludeFromRandom),
          HasVersionSpecific: Boolean(game.HasVersionSpecific),
        };
      });
    } catch (error) {
      console.error('Error getting game:', error);
      throw error;
    }
  });

  // ===========================================================================
  // USER ANNOTATION OPERATIONS (clientdata.db)
  // ===========================================================================

  /**
   * Save game annotation (game-wide)
   * Channel: db:clientdata:set:annotation
   */
  ipcMain.handle('db:clientdata:set:annotation', async (event, annotation) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const {
        gameid,
        status,
        myDifficultyRating,
        myReviewRating,
        mySkillRating,
        hidden,
        excludeFromRandom,
        mynotes
      } = annotation;
      
      // Validate inputs
      if (!gameid || typeof gameid !== 'string') {
        throw new Error('Invalid gameid');
      }
      
      if (myDifficultyRating !== null && myDifficultyRating !== undefined) {
        if (myDifficultyRating < 0 || myDifficultyRating > 5) {
          throw new Error('Difficulty rating must be 0-5');
        }
      }
      
      if (myReviewRating !== null && myReviewRating !== undefined) {
        if (myReviewRating < 0 || myReviewRating > 5) {
          throw new Error('Review rating must be 0-5');
        }
      }
      
      if (mySkillRating !== null && mySkillRating !== undefined) {
        if (mySkillRating < 0 || mySkillRating > 10) {
          throw new Error('Skill rating must be 0-10');
        }
      }
      
      db.prepare(`
        INSERT OR REPLACE INTO user_game_annotations
          (gameid, status, user_difficulty_rating, user_review_rating, user_skill_rating,
           hidden, exclude_from_random, user_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        gameid,
        status || 'Default',
        myDifficultyRating,
        myReviewRating,
        mySkillRating,
        hidden ? 1 : 0,
        excludeFromRandom ? 1 : 0,
        mynotes || null
      );
      
      return { success: true };
    } catch (error) {
      console.error('Error saving annotation:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Save version-specific annotation
   * Channel: db:clientdata:set:version-annotation
   */
  ipcMain.handle('db:clientdata:set:version-annotation', async (event, annotation) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const {
        gameid,
        version,
        status,
        myDifficultyRating,
        myReviewRating,
        mySkillRating,
        mynotes
      } = annotation;
      
      if (!gameid || version === null || version === undefined) {
        throw new Error('Invalid gameid or version');
      }
      
      const annotationKey = `${gameid}-${version}`;
      
      db.prepare(`
        INSERT OR REPLACE INTO user_game_version_annotations
          (annotation_key, gameid, version, status, 
           user_difficulty_rating, user_review_rating, user_skill_rating, user_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        annotationKey,
        gameid,
        version,
        status,
        myDifficultyRating,
        myReviewRating,
        mySkillRating,
        mynotes
      );
      
      return { success: true };
    } catch (error) {
      console.error('Error saving version annotation:', error);
      return { success: false, error: error.message };
    }
  });

  // ===========================================================================
  // STAGE OPERATIONS (clientdata.db)
  // ===========================================================================

  /**
   * Get stages for a game with user annotations
   * Channel: db:clientdata:get:stages
   */
  ipcMain.handle('db:clientdata:get:stages', async (event, { gameid }) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const stages = db.prepare(`
        SELECT 
          gs.stage_key as key,
          gs.gameid as parentId,
          gs.exit_number as exitNumber,
          gs.description,
          gs.public_rating as publicRating,
          usa.user_difficulty_rating as myDifficultyRating,
          usa.user_review_rating as myReviewRating,
          usa.user_skill_rating as mySkillRating,
          usa.user_notes as myNotes
        FROM game_stages gs
        LEFT JOIN user_stage_annotations usa ON gs.stage_key = usa.stage_key
        WHERE gs.gameid = ?
        ORDER BY gs.exit_number
      `).all(gameid);
      
      return stages;
    } catch (error) {
      console.error('Error getting stages:', error);
      return [];
    }
  });

  /**
   * Save stage annotation
   * Channel: db:clientdata:set:stage-annotation
   */
  ipcMain.handle('db:clientdata:set:stage-annotation', async (event, annotation) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const {
        gameid,
        exitNumber,
        myDifficultyRating,
        myReviewRating,
        mySkillRating,
        myNotes
      } = annotation;
      
      if (!gameid || !exitNumber) {
        throw new Error('Invalid gameid or exitNumber');
      }
      
      const stageKey = `${gameid}-${exitNumber}`;
      
      db.prepare(`
        INSERT OR REPLACE INTO user_stage_annotations
          (stage_key, gameid, exit_number, user_difficulty_rating, 
           user_review_rating, user_skill_rating, user_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `).run(
        stageKey,
        gameid,
        exitNumber,
        myDifficultyRating,
        myReviewRating,
        mySkillRating,
        myNotes
      );
      
      return { success: true };
    } catch (error) {
      console.error('Error saving stage annotation:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Bulk save stage annotations
   * Channel: db:clientdata:set:stage-annotations-bulk
   */
  ipcMain.handle('db:clientdata:set:stage-annotations-bulk', async (event, { annotations }) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const transaction = db.transaction((annotationList) => {
        const stmt = db.prepare(`
          INSERT OR REPLACE INTO user_stage_annotations
            (stage_key, gameid, exit_number, user_difficulty_rating, 
             user_review_rating, user_skill_rating, user_notes)
          VALUES (?, ?, ?, ?, ?, ?, ?)
        `);
        
        for (const ann of annotationList) {
          const stageKey = `${ann.gameid}-${ann.exitNumber}`;
          stmt.run(
            stageKey,
            ann.gameid,
            ann.exitNumber,
            ann.myDifficultyRating,
            ann.myReviewRating,
            ann.mySkillRating,
            ann.myNotes
          );
        }
      });
      
      transaction(annotations);
      
      return { success: true };
    } catch (error) {
      console.error('Error saving stage annotations:', error);
      return { success: false, error: error.message };
    }
  });

  // ===========================================================================
  // SETTINGS OPERATIONS (clientdata.db csettings table)
  // ===========================================================================

  /**
   * Get all settings
   * Channel: db:settings:get:all
   */
  ipcMain.handle('db:settings:get:all', async () => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const rows = db.prepare(`
        SELECT csetting_name, csetting_value
        FROM csettings
      `).all();
      
      // Convert to object
      const settings = {};
      rows.forEach(row => {
        settings[row.csetting_name] = row.csetting_value;
      });
      
      return settings;
    } catch (error) {
      console.error('Error getting settings:', error);
      return {};
    }
  });

  /**
   * Set a single setting
   * Channel: db:settings:set:value
   */
  ipcMain.handle('db:settings:set:value', async (event, { name, value }) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const uuid = crypto.randomUUID();
      
      db.prepare(`
        INSERT INTO csettings (csettinguid, csetting_name, csetting_value)
        VALUES (?, ?, ?)
        ON CONFLICT(csetting_name) DO UPDATE SET csetting_value = excluded.csetting_value
      `).run(uuid, name, value);
      
      return { success: true };
    } catch (error) {
      console.error('Error setting value:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Save multiple settings at once
   * Channel: db:settings:set:bulk
   */
  ipcMain.handle('db:settings:set:bulk', async (event, { settings }) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const transaction = db.transaction((settingsObj) => {
        const stmt = db.prepare(`
          INSERT INTO csettings (csettinguid, csetting_name, csetting_value)
          VALUES (?, ?, ?)
          ON CONFLICT(csetting_name) DO UPDATE SET csetting_value = excluded.csetting_value
        `);
        
        Object.entries(settingsObj).forEach(([name, value]) => {
          const uuid = crypto.randomUUID();
          stmt.run(uuid, name, String(value));
        });
      });
      
      transaction(settings);
      
      return { success: true };
    } catch (error) {
      console.error('Error saving settings:', error);
      return { success: false, error: error.message };
    }
  });

  // ===========================================================================
  // RUN SYSTEM OPERATIONS (clientdata.db)
  // ===========================================================================

  /**
   * Create a new run
   * Channel: db:runs:create
   */
  ipcMain.handle('db:runs:create', async (event, { runName, runDescription, globalConditions }) => {
    try {
      const db = dbManager.getConnection('clientdata');
      const runUuid = crypto.randomUUID();
      
      db.prepare(`
        INSERT INTO runs (run_uuid, run_name, run_description, status, global_conditions)
        VALUES (?, ?, ?, 'preparing', ?)
      `).run(runUuid, runName, runDescription, JSON.stringify(globalConditions || []));
      
      return { success: true, runUuid };
    } catch (error) {
      console.error('Error creating run:', error);
      return { success: false, error: error.message };
    }
  });

  /**
   * Save run plan entries
   * Channel: db:runs:save-plan
   */
  ipcMain.handle('db:runs:save-plan', async (event, { runUuid, entries }) => {
    try {
      const db = dbManager.getConnection('clientdata');
      
      const transaction = db.transaction((runId, entryList) => {
        // Clear existing entries
        db.prepare(`DELETE FROM run_plan_entries WHERE run_uuid = ?`).run(runId);
        
        // Insert new entries
        const stmt = db.prepare(`
          INSERT INTO run_plan_entries
            (entry_uuid, run_uuid, sequence_number, entry_type, gameid, exit_number,
             count, filter_difficulty, filter_type, filter_pattern, filter_seed, conditions)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);
        
        entryList.forEach((entry, idx) => {
          const entryUuid = crypto.randomUUID();
          stmt.run(
            entryUuid,
            runId,
            idx + 1,
            entry.entryType,
            entry.id !== '(random)' ? entry.id : null,
            entry.stageNumber || null,
            entry.count || 1,
            entry.filterDifficulty || null,
            entry.filterType || null,
            entry.filterPattern || null,
            entry.seed || null,
            JSON.stringify(entry.conditions || [])
          );
        });
      });
      
      transaction(runUuid, entries);
      
      return { success: true };
    } catch (error) {
      console.error('Error saving run plan:', error);
      return { success: false, error: error.message };
    }
  });

  console.log('IPC handlers registered successfully');
}

module.exports = { registerDatabaseHandlers };

