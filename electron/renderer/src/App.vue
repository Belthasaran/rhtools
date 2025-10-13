<template>
  <main class="layout">
    <header class="toolbar">
      <div class="left-controls">
        <button @click="openSettings">Open settings</button>

        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search or filter..."
          class="search"
        />
        <button @click="clearFilters" :disabled="!hasActiveFilters">Clear filters</button>

        <button @click="checkAllVisible" :disabled="filteredItems.length === 0">Check all</button>
        <button @click="uncheckAll">Uncheck all</button>
        <button @click="checkRandom" :disabled="filteredItems.length === 0">Check random</button>
        <button @click="addSelectedToRun" :disabled="numChecked === 0">Add to Run</button>
        <button @click="hideChecked" :disabled="numChecked === 0">Hide checked</button>
        <button @click="unhideChecked" :disabled="numChecked === 0">Unhide checked</button>

        <label class="status-setter">
          Status for checked:
          <select v-model="bulkStatus" @change="applyBulkStatus" :disabled="numChecked === 0">
            <option value="">Select…</option>
            <option value="Default">Default</option>
            <option value="In Progress">In Progress</option>
            <option value="Finished">Finished</option>
          </select>
        </label>

        <label class="toggle">
          <input type="checkbox" v-model="showHidden" /> Show hidden
        </label>
        <label class="toggle">
          <input type="checkbox" v-model="hideFinished" /> Hide finished
        </label>
      </div>

      <div class="right-actions">
        <button @click="openRunModal">Prepare Run</button>
        <button @click="startSelected" :disabled="!canStartGames">Start</button>
        <button @click="editNotes" :disabled="!exactlyOneSelected">Edit notes</button>
        <button @click="setMyRating" :disabled="!exactlyOneSelected">My rating</button>
      </div>
    </header>

    <section class="content">
      <div class="table-wrapper">
        <!-- Loading indicator -->
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <div>Loading games from database...</div>
        </div>
        
        <!-- Error message -->
        <div v-if="loadError" class="error-message">
          <strong>Error:</strong> {{ loadError }}
          <button @click="loadGames">Retry</button>
        </div>
        
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-check">
                <input type="checkbox" :checked="allVisibleChecked" @change="toggleCheckAll($event)" />
              </th>
              <th>Action</th>
              <th>Id</th>
              <th>Name</th>
              <th>Type</th>
              <th>Author</th>
              <th>Length</th>
              <th>Status</th>
              <th>My Ratings</th>
              <th>Public</th>
              <th>Hidden</th>
              <th>My notes</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in filteredItems"
              :key="row.Id"
              :class="{ hidden: row.Hidden, finished: row.Status === 'Finished' }"
              @click="rowClick(row)"
            >
              <td class="col-check">
                <input type="checkbox" :checked="selectedIds.has(row.Id)" @change="toggleMainSelection(row.Id, $event)" @click.stop />
              </td>
              <td class="action">{{ isInRun(row.Id) ? '*' : '' }}</td>
              <td>{{ row.Id }}</td>
              <td class="name" :class="{ 'in-run': isInRun(row.Id) }">{{ row.Name }}</td>
              <td>{{ row.Type }}</td>
              <td>{{ row.Author }}</td>
              <td>{{ row.Length }}</td>
              <td>{{ row.Status }}</td>
              <td>{{ formatRatings(row.MyDifficultyRating, row.MyReviewRating) }}</td>
              <td>{{ row.Publicrating ?? '' }}</td>
              <td>{{ row.Hidden ? 'Yes' : 'No' }}</td>
              <td class="notes">{{ row.Mynotes ?? '' }}</td>
            </tr>
            <tr v-if="filteredItems.length === 0">
              <td class="empty" colspan="11">No items match your filters.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <aside class="sidebar">
        <div class="panel" v-if="exactlyOneSelected && selectedItem">
          <h3>Details</h3>
          <div class="panel-body details">
            <table class="kv-table">
              <tbody>
                <!-- Version Selector -->
                <tr>
                  <th>Version</th>
                  <td>
                    <select v-model="selectedVersion">
                      <option v-for="v in availableVersions" :key="v" :value="v">
                        Version {{ v }}{{ v === latestVersion ? ' (Latest)' : '' }}
                      </option>
                    </select>
                  </td>
                </tr>
                
                <!-- Official Fields (READ-ONLY) -->
                <tr><th>Id</th><td class="readonly-field">{{ selectedItem.Id }}</td></tr>
                <tr><th>Name</th><td class="readonly-field">{{ selectedItem.Name }}</td></tr>
                <tr><th>Type</th><td class="readonly-field">{{ selectedItem.Type }}</td></tr>
                <tr v-if="selectedItem.LegacyType"><th>Legacy Type</th><td class="readonly-field">{{ selectedItem.LegacyType }}</td></tr>
                <tr><th>Author</th><td class="readonly-field">{{ selectedItem.Author }}</td></tr>
                <tr><th>Length</th><td class="readonly-field">{{ selectedItem.Length }}</td></tr>
                <tr><th>Public Difficulty</th><td class="readonly-field">{{ selectedItem.PublicDifficulty || '—' }}</td></tr>
                <tr><th>Public Rating</th><td class="readonly-field">{{ selectedItem.Publicrating || '—' }}</td></tr>
                
                <!-- User-Editable Fields -->
                <tr>
                  <th>Status</th>
                  <td>
                    <select v-model="selectedItem.Status">
                      <option value="Default">Default</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Finished">Finished</option>
                    </select>
                  </td>
                </tr>
                
                <!-- Dual Ratings with Star Picker (0-5 scale) -->
                <tr>
                  <th>My Difficulty</th>
                  <td>
                    <div class="star-rating">
                      <span 
                        v-for="n in 6" 
                        :key="'diff-' + (n-1)"
                        @click="selectedItem.MyDifficultyRating = n - 1"
                        :class="{ filled: (n - 1) <= (selectedItem.MyDifficultyRating ?? -1) }"
                        class="star"
                      >★</span>
                      <button @click="selectedItem.MyDifficultyRating = null" class="btn-clear-rating">✕</button>
                      <span class="rating-label">{{ difficultyLabel(selectedItem.MyDifficultyRating) }}</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <th>My Review</th>
                  <td>
                    <div class="star-rating">
                      <span 
                        v-for="n in 6" 
                        :key="'rev-' + (n-1)"
                        @click="selectedItem.MyReviewRating = n - 1"
                        :class="{ filled: (n - 1) <= (selectedItem.MyReviewRating ?? -1) }"
                        class="star"
                      >★</span>
                      <button @click="selectedItem.MyReviewRating = null" class="btn-clear-rating">✕</button>
                      <span class="rating-label">{{ reviewLabel(selectedItem.MyReviewRating) }}</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <th>My Skill Level</th>
                  <td>
                    <div class="skill-rating-container">
                      <div class="star-rating skill-rating">
                        <span 
                          v-for="n in 11" 
                          :key="'skill-' + (n-1)"
                          @click="selectedItem.MySkillRating = n - 1"
                          :class="{ filled: (n - 1) <= (selectedItem.MySkillRating ?? -1) }"
                          :title="skillRatingHoverText(n - 1)"
                          class="star star-small"
                        >★</span>
                        <button @click="selectedItem.MySkillRating = null" class="btn-clear-rating">✕</button>
                        <span class="rating-label">{{ skillLabel(selectedItem.MySkillRating) }}</span>
                      </div>
                      <div class="skill-caption" v-if="selectedItem.MySkillRating !== null && selectedItem.MySkillRating !== undefined">
                        {{ skillRatingHoverText(selectedItem.MySkillRating) }}
                      </div>
                    </div>
                  </td>
                </tr>
                
                <tr>
                  <th>Hidden</th>
                  <td><input type="checkbox" v-model="selectedItem.Hidden" /></td>
                </tr>
                <tr>
                  <th>Exclude from Random</th>
                  <td><input type="checkbox" v-model="selectedItem.ExcludeFromRandom" /></td>
                </tr>
                <tr>
                  <th>My notes</th>
                  <td><textarea v-model="selectedItem.Mynotes" rows="4"></textarea></td>
                </tr>
                
                <!-- Action Buttons -->
                <tr>
                  <td colspan="2" style="padding-top: 12px;">
                    <div class="detail-actions">
                      <button @click="setVersionSpecificRating" :disabled="isVersionSpecific">
                        {{ isVersionSpecific ? '✓ Version-Specific' : 'Set Version-Specific Rating' }}
                      </button>
                      <button @click="viewJsonDetails">View Details (JSON)</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="panel" v-if="exactlyOneSelected && selectedItem">
          <h3>Stages</h3>
          <div class="panel-actions">
            <button @click="addStagesToRun" :disabled="selectedStageIds.size === 0">Add chosen stages to run</button>
            <button @click="editStageNotes" :disabled="selectedStageIds.size === 0">Edit notes</button>
            <button @click="setStageRating('difficulty')" :disabled="selectedStageIds.size === 0">Set Difficulty</button>
            <button @click="setStageRating('review')" :disabled="selectedStageIds.size === 0">Set Review</button>
          </div>
          <div class="panel-body stages">
            <table class="data-table">
              <thead>
                <tr>
                  <th class="col-check">
                    <input type="checkbox" :checked="allStagesChecked" @change="toggleCheckAllStages($event)" />
                  </th>
                  <th>Parent ID</th>
                  <th>Exit #</th>
                  <th>Description</th>
                  <th>Public</th>
                  <th>My Ratings</th>
                  <th>My notes</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="st in currentStages" :key="st.key">
                  <td class="col-check"><input type="checkbox" :checked="selectedStageIds.has(st.key)" @change="toggleStageSelection(st.key, $event)" /></td>
                  <td>{{ st.parentId }}</td>
                  <td>{{ st.exitNumber }}</td>
                  <td>{{ st.description }}</td>
                  <td>{{ st.publicRating ?? '' }}</td>
                  <td>{{ formatRatings(st.myDifficultyRating, st.myReviewRating) }}</td>
                  <td>{{ st.myNotes ?? '' }}</td>
                </tr>
                <tr v-if="currentStages.length === 0">
                  <td class="empty" colspan="7">No stages.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="panel" v-if="!exactlyOneSelected">
          <h3>Details</h3>
          <div class="panel-body">Select a single item to view details and stages.</div>
        </div>
      </aside>
    </section>
  </main>
  
  <!-- Prepare Run Modal -->
  <div v-if="runModalOpen" class="modal-backdrop" @click.self="closeRunModal">
    <div class="modal">
      <header class="modal-header">
        <h3>{{ isRunActive ? 'Active Run' : 'Prepare Run' }}{{ currentRunName ? ': ' + currentRunName : '' }}</h3>
        <div class="modal-header-actions">
          <!-- Preparing state -->
          <template v-if="!isRunActive">
            <button @click="editGlobalConditions" class="btn-conditions-header" :title="`Global Conditions: ${globalRunConditions.length > 0 ? globalRunConditions.join(', ') : 'None'}`">
              {{ globalRunConditions.length > 0 ? `✓ Global Conditions (${globalRunConditions.length})` : 'Set Global Conditions' }}
            </button>
            <button @click="exportRunToFile" :disabled="!isRunSaved">📤 Export</button>
            <button @click="importRunFromFile">📥 Import</button>
            <button @click="stageRun('save')" :disabled="runEntries.length === 0">Stage and Save</button>
            <button @click="startRun" :disabled="!isRunSaved" class="btn-start-run">▶ Start Run</button>
          </template>
          <!-- Active state -->
          <template v-if="isRunActive">
            <span class="run-timer">⏱ {{ formatTime(runElapsedSeconds) }}</span>
            <span class="pause-time" v-if="runPauseSeconds > 0">⏸ {{ formatTime(runPauseSeconds) }}</span>
            <span class="run-progress">Challenge {{ currentChallengeIndex + 1 }} / {{ runEntries.length }}</span>
            <button @click="pauseRun" v-if="!isRunPaused" class="btn-pause">⏸ Pause</button>
            <button @click="unpauseRun" v-if="isRunPaused" class="btn-unpause">▶ Unpause</button>
            <button @click="undoChallenge" :disabled="!canUndo || isRunPaused" class="btn-back">↶ Back</button>
            <button @click="nextChallenge" :disabled="!currentChallenge || isRunPaused" class="btn-next">✓ Done</button>
            <button @click="skipChallenge" :disabled="!currentChallenge || isRunPaused" class="btn-skip">⏭ Skip</button>
            <button @click="cancelRun" class="btn-cancel-run">✕ Cancel Run</button>
          </template>
          <button class="close" @click="closeRunModal">✕</button>
        </div>
      </header>

      <!-- Toolbar only shown when preparing -->
      <section v-if="!isRunActive" class="modal-toolbar">
        <div class="left">
          <button @click="checkAllRun">Check All</button>
          <button @click="uncheckAllRun">Uncheck All</button>
          <button @click="removeCheckedRun" :disabled="checkedRunCount === 0">Remove</button>
          <button @click="moveCheckedUp" :disabled="!canMoveCheckedUp">↑ Move Up</button>
          <button @click="moveCheckedDown" :disabled="!canMoveCheckedDown">↓ Move Down</button>
        </div>
        <div class="right add-random">
          <label>
            Filter Type
            <select v-model="randomFilter.type">
              <option value="any">Any</option>
              <option value="standard">Standard</option>
              <option value="kaizo">Kaizo</option>
              <option value="traditional">Traditional</option>
            </select>
          </label>
          <label>
            Difficulty
            <select v-model="randomFilter.difficulty">
              <option value="any">Any</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="expert">Expert</option>
            </select>
          </label>
          <input class="pattern" v-model="randomFilter.pattern" type="text" placeholder="Optional filter pattern" />
          <label>
            Count
            <input class="count" v-model.number="randomFilter.count" type="number" min="1" max="100" />
          </label>
          <label>
            Seed
            <input class="seed" v-model="randomFilter.seed" type="text" placeholder="Auto-generated" />
          </label>
          <button @click="regenerateSeed" title="Generate new random seed">🎲</button>
          <button @click="addRandomGameToRun" :disabled="!isRandomAddValid">Add Random Game</button>
        </div>
      </section>

      <section class="modal-body">
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th class="col-check">
                  <input type="checkbox" :checked="allRunChecked" @change="toggleCheckAllRun($event)" />
                </th>
                <th class="col-seq">#</th>
                <th v-if="isRunActive" class="col-status">Status</th>
                <th v-if="isRunActive" class="col-duration">Time</th>
                <th class="col-actions">Actions</th>
                <th>ID</th>
                <th>Entry Type</th>
                <th>Name</th>
                <th>Stage #</th>
                <th>Stage name</th>
                <th class="col-count">Count</th>
                <th>Filter difficulty</th>
                <th>Filter type</th>
              <th class="col-pattern">Filter pattern</th>
              <th class="col-seed">Seed</th>
              <th class="col-conditions">Conditions</th>
            </tr>
          </thead>
          <tbody>
              <tr 
                v-for="(entry, idx) in runEntries" 
                :key="entry.key"
                :draggable="!isRunActive"
                @dragstart="handleDragStart(idx, $event)"
                @dragover.prevent="handleDragOver(idx, $event)"
                @drop="handleDrop(idx, $event)"
                @dragend="handleDragEnd"
                :class="{ 
                  'dragging': draggedIndex === idx,
                  'current-challenge': isRunActive && idx === currentChallengeIndex
                }"
              >
                <td class="col-check">
                  <input type="checkbox" :checked="checkedRun.has(entry.key)" @change="toggleRunEntrySelection(entry.key, $event)" :disabled="isRunActive" />
                </td>
                <td class="col-seq">{{ idx + 1 }}</td>
                <td v-if="isRunActive" class="col-status" :class="getChallengeStatusClass(idx)">
                  <span class="status-icon">{{ getChallengeStatusIcon(idx) }}</span>
                </td>
                <td v-if="isRunActive" class="col-duration">
                  {{ getChallengeDuration(idx) }}
                </td>
                <td class="col-actions">
                  <button class="btn-mini" @click="moveRowUp(idx)" :disabled="isRunActive || idx === 0" title="Move up">↑</button>
                  <button class="btn-mini" @click="moveRowDown(idx)" :disabled="isRunActive || idx === runEntries.length - 1" title="Move down">↓</button>
                </td>
                <td>{{ entry.id }}</td>
                <td>
                  <select v-model="entry.entryType" :disabled="isRunActive || entry.isLocked">
                    <option value="game" v-if="entry.isLocked && entry.entryType === 'game'">Game</option>
                    <option value="stage" v-if="entry.isLocked && entry.entryType === 'stage'">Stage</option>
                    <option value="random_game" v-if="!entry.isLocked || entry.entryType === 'random_game'">Random Game</option>
                    <option value="random_stage" v-if="!entry.isLocked || entry.entryType === 'random_stage'">Random Stage</option>
                  </select>
                </td>
                <td>{{ entry.name }}</td>
                <td>{{ entry.stageNumber ?? '' }}</td>
                <td>{{ entry.stageName ?? '' }}</td>
                <td class="col-count"><input type="number" min="1" v-model.number="entry.count" :disabled="isRunActive" /></td>
                <td v-if="isRandomEntry(entry)">
                  <select v-model="entry.filterDifficulty" :disabled="isRunActive">
                    <option value="">—</option>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="expert">Expert</option>
                  </select>
                </td>
                <td v-else>—</td>
                <td v-if="isRandomEntry(entry)">
                  <select v-model="entry.filterType" :disabled="isRunActive">
                    <option value="">—</option>
                    <option value="standard">Standard</option>
                    <option value="kaizo">Kaizo</option>
                    <option value="traditional">Traditional</option>
                  </select>
                </td>
                <td v-else>—</td>
                <td class="col-pattern" v-if="isRandomEntry(entry)"><input v-model="entry.filterPattern" :disabled="isRunActive" /></td>
                <td class="col-pattern" v-else>—</td>
                <td class="col-seed" v-if="isRandomEntry(entry)"><input v-model="entry.seed" :disabled="isRunActive" /></td>
                <td class="col-seed" v-else>—</td>
                <td class="col-conditions">
                  <button @click="editConditions(entry)" class="btn-mini btn-conditions" :disabled="isRunActive" :title="`Conditions: ${entry.conditions.length > 0 ? entry.conditions.join(', ') : 'None'}`">
                    {{ entry.conditions.length > 0 ? `✓ (${entry.conditions.length})` : 'Set' }}
                  </button>
                </td>
              </tr>
              <tr v-if="runEntries.length === 0">
                <td class="empty" colspan="14">Run is empty. Add entries or use Add Random Game.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>

  <!-- JSON Details Modal -->
  <div v-if="jsonModalOpen" class="modal-backdrop" @click.self="closeJsonModal">
    <div class="modal json-modal">
      <header class="modal-header">
        <h3>Game Details (JSON)</h3>
        <button class="close" @click="closeJsonModal">✕</button>
      </header>
      <section class="modal-body json-body">
        <pre>{{ jsonDetailsContent }}</pre>
      </section>
      <footer class="modal-footer">
        <button @click="closeJsonModal">Close</button>
      </footer>
    </div>
  </div>

  <!-- Settings Modal -->
  <div v-if="settingsModalOpen" class="modal-backdrop" @click.self="closeSettings">
    <div class="modal settings-modal">
      <header class="modal-header">
        <h3>Settings</h3>
        <button class="close" @click="closeSettings">✕</button>
      </header>

      <section class="modal-body settings-body">
        <!-- Theme Setting -->
        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">
              Theme
            </label>
            <div class="setting-control">
              <select v-model="settings.theme" @change="onThemeChange">
                <option value="light">Light Theme</option>
                <option value="dark">Dark</option>
                <option value="onyx">Onyx (Black & Gray)</option>
                <option value="ash">Ash (Mid-Gray)</option>
              </select>
            </div>
          </div>
          <div class="setting-caption">
            Choose your preferred color scheme. Changes apply immediately.
          </div>
        </div>

        <!-- Text Size Setting -->
        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">
              Text Size
            </label>
            <div class="setting-control">
              <input 
                type="range" 
                v-model.number="textSizeSliderValue" 
                @input="onTextSizeChange"
                min="0" 
                max="3" 
                step="1" 
                class="text-size-slider"
              />
              <span class="text-size-label">{{ getTextSizeDisplayName(settings.textSize) }}</span>
            </div>
          </div>
          <div class="setting-caption">
            Adjust the text size throughout the application.
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">
              <span class="status-icon">{{ settings.vanillaRomValid ? '✓' : '' }}</span>
              Import required Vanilla SMW ROM
            </label>
            <div class="setting-control">
              <div 
                class="drop-zone"
                @dragover.prevent
                @drop.prevent="handleRomDrop"
              >
                Drag ROM file here
              </div>
              <button @click="browseRomFile">Browse</button>
            </div>
          </div>
          <div v-if="settings.vanillaRomPath" class="setting-current-path">
            Current: <code>{{ settings.vanillaRomPath }}</code>
          </div>
          <div class="setting-caption">
            You must have a legally-obtained SMW SFC file that you are authorized to play with, required to proceed.<br>
            The acceptable file has a sha224 sum of <code>fdc4c00e09a8e08d395003e9c8a747f45a9e5e94cbfedc508458eb08</code><br>
            OR sha-1: <code>6b47bb75d16514b6a476aa0c73a683a2a4c18765</code>, Or Md5: <code>cdd3c8c37322978ca8669b34bc89c804</code>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">
              <span class="status-icon">{{ settings.flipsValid ? '✓' : '' }}</span>
              Import FLIPS executable
            </label>
            <div class="setting-control">
              <div 
                class="drop-zone"
                @dragover.prevent
                @drop.prevent="handleFlipsDrop"
              >
                Drag FLIPS file here
              </div>
              <button @click="browseFlipsFile">Browse</button>
            </div>
          </div>
          <div v-if="settings.flipsPath" class="setting-current-path">
            Current: <code>{{ settings.flipsPath }}</code>
          </div>
          <div class="setting-caption">
            Floating IPS <a href="https://www.gamebrew.org/wiki/Floating_IPS" target="_blank">https://www.gamebrew.org/wiki/Floating_IPS</a>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">Game launch method</label>
            <div class="setting-control">
              <select v-model="settings.launchMethod">
                <option value="manual">Launch Manually</option>
                <option value="program">Run Launch Program</option>
                <option value="usb2snes">Launch from USB2Snes</option>
              </select>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">Launch Program</label>
            <div class="setting-control">
              <div 
                class="drop-zone"
                @dragover.prevent
                @drop.prevent="handleLaunchProgramDrop"
              >
                Drag program file here
              </div>
              <button @click="browseLaunchProgram">Browse</button>
            </div>
          </div>
          <div v-if="settings.launchProgram" class="setting-current-path">
            Current: <code>{{ settings.launchProgram }}</code>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">Launch Program Arguments</label>
            <div class="setting-control">
              <input type="text" v-model="settings.launchProgramArgs" />
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">USB2snes Websocket address</label>
            <div class="setting-control">
              <input type="text" v-model="settings.usb2snesAddress" />
            </div>
          </div>
          <div class="setting-caption warning">
            ⚠ USB2SNES launch requires a USB2SNES server running. <a href="https://usb2snes.com/" target="_blank">https://usb2snes.com/</a>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">USB2SNES Enabled</label>
            <div class="setting-control">
              <select v-model="settings.usb2snesEnabled">
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">USB2SNES Launch Preference</label>
            <div class="setting-control">
              <select v-model="settings.usb2snesLaunchPref">
                <option value="auto">Launch Automatically</option>
                <option value="manual">Manual Launch (Do nothing)</option>
                <option value="reset">Manual Launch (Reset console)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">USB2SNES Upload Preference</label>
            <div class="setting-control">
              <select v-model="settings.usb2snesUploadPref">
                <option value="manual">Manual Transfer (do not upload)</option>
                <option value="check">Check first and Upload</option>
                <option value="always">Always Upload</option>
              </select>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">USB2SNES Upload Directory</label>
            <div class="setting-control">
              <input type="text" v-model="settings.usb2snesUploadDir" />
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">
              <span class="status-icon">{{ settings.asarValid ? '✓' : '' }}</span>
              Import ASAR executable
            </label>
            <div class="setting-control">
              <div 
                class="drop-zone"
                @dragover.prevent
                @drop.prevent="handleAsarDrop"
              >
                Drag ASAR file here
              </div>
              <button @click="browseAsarFile">Browse</button>
            </div>
          </div>
          <div v-if="settings.asarPath" class="setting-current-path">
            Current: <code>{{ settings.asarPath }}</code>
          </div>
          <div class="setting-caption">
            Download ASAR from <a href="https://smwc.me/s/37443" target="_blank">https://smwc.me/s/37443</a>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">
              <span class="status-icon">{{ settings.uberAsmValid ? '✓' : '' }}</span>
              Import UberASM executable
            </label>
            <div class="setting-control">
              <div 
                class="drop-zone"
                @dragover.prevent
                @drop.prevent="handleUberAsmDrop"
              >
                Drag UberASM file here
              </div>
              <button @click="browseUberAsmFile">Browse</button>
            </div>
          </div>
          <div v-if="settings.uberAsmPath" class="setting-current-path">
            Current: <code>{{ settings.uberAsmPath }}</code>
          </div>
          <div class="setting-caption">
            Download UberASM from <a href="https://smwc.me/s/39036" target="_blank">https://smwc.me/s/39036</a>
          </div>
        </div>

        <div class="settings-section">
          <div class="setting-row">
            <label class="setting-label">
              <span class="status-icon">{{ settings.tempDirValid ? '✓' : '✗' }}</span>
              Temporary Directory Override
            </label>
            <div class="setting-control">
              <input type="text" v-model="settings.tempDirOverride" placeholder="Leave blank for OS default temp dir" />
            </div>
          </div>
          <div v-if="settings.tempDirOverride" class="setting-current-path">
            Current: <code>{{ settings.tempDirOverride }}</code>
          </div>
          <div class="setting-caption">
            Optional: Override the base path for temporary directories used by RHTools.<br>
            Leave blank to use the OS-specific temporary directory. If specified, the path must exist.
          </div>
        </div>
      </section>

      <footer class="modal-footer">
        <button @click="saveSettings" class="btn-primary">Save Changes and Close</button>
      </footer>
    </div>
  </div>

  <!-- Run Name Input Modal -->
  <div v-if="runNameModalOpen" class="modal-backdrop" @click.self="cancelRunName">
    <div class="modal run-name-modal">
      <header class="modal-header">
        <h3>Enter Run Name</h3>
        <button class="close" @click="cancelRunName">✕</button>
      </header>
      <section class="modal-body run-name-body">
        <label for="run-name-input">Run Name:</label>
        <input 
          id="run-name-input"
          type="text" 
          v-model="runNameInput" 
          placeholder="My Challenge Run"
          @keyup.enter="confirmRunName"
          autofocus
        />
      </section>
      <footer class="modal-footer">
        <button @click="confirmRunName" class="btn-primary">Save Run</button>
        <button @click="cancelRunName">Cancel</button>
      </footer>
    </div>
  </div>

  <!-- Resume Run Modal (on app startup) -->
  <div v-if="resumeRunModalOpen" class="modal-backdrop">
    <div class="modal resume-run-modal">
      <header class="modal-header">
        <h3>⚠ Active Run Found</h3>
      </header>
      <section class="modal-body resume-run-body">
        <p class="resume-message">You have an active run in progress:</p>
        <div class="run-info">
          <div class="run-info-row">
            <span class="label">Run Name:</span>
            <span class="value">{{ resumeRunData?.run_name }}</span>
          </div>
          <div class="run-info-row">
            <span class="label">Status:</span>
            <span class="value">{{ resumeRunData?.isPaused ? '⏸ Paused' : '▶ Running' }}</span>
          </div>
          <div class="run-info-row">
            <span class="label">Elapsed Time:</span>
            <span class="value">⏱ {{ formatTime(resumeRunData?.elapsedSeconds || 0) }}</span>
          </div>
          <div class="run-info-row" v-if="resumeRunData?.pause_seconds > 0">
            <span class="label">Paused Time:</span>
            <span class="value pause-time">⏸ {{ formatTime(resumeRunData?.pause_seconds || 0) }}</span>
          </div>
        </div>
        <p class="resume-prompt">What would you like to do?</p>
      </section>
      <footer class="modal-footer resume-run-footer">
        <button @click="resumeRunFromStartup" class="btn-primary btn-large">▶ Resume Run</button>
        <button @click="pauseRunFromStartup" class="btn-secondary btn-large">⏸ View (Paused)</button>
        <button @click="cancelRunFromStartup" class="btn-danger btn-large">✕ Cancel Run</button>
      </footer>
    </div>
  </div>

  <!-- Staging Progress Modal -->
  <div v-if="stagingProgressModalOpen" class="modal-backdrop">
    <div class="modal staging-progress-modal">
      <header class="modal-header">
        <h3>🎮 Staging Run Games...</h3>
      </header>
      <section class="modal-body">
        <div class="progress-info">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: (stagingProgressCurrent / stagingProgressTotal * 100) + '%' }"></div>
          </div>
          <p class="progress-text">{{ stagingProgressCurrent }} / {{ stagingProgressTotal }}</p>
          <p class="progress-game">{{ stagingProgressGameName }}</p>
        </div>
      </section>
    </div>
  </div>

  <!-- Staging Success Modal -->
  <div v-if="stagingSuccessModalOpen" class="modal-backdrop">
    <div class="modal staging-success-modal">
      <header class="modal-header">
        <h3>✅ Run Staged Successfully!</h3>
      </header>
      <section class="modal-body">
        <div class="success-info">
          <p class="success-message">
            <strong>{{ stagingSfcCount }}</strong> game files have been prepared for your run.
          </p>
          <div class="folder-info">
            <label class="folder-label">Run Folder:</label>
            <div class="folder-path">
              <input type="text" readonly :value="stagingFolderPath" class="folder-path-input" />
              <button @click="openStagingFolder" class="btn-open-folder" title="Open Folder">📁</button>
            </div>
          </div>

          <!-- Conditional action buttons based on settings -->
          <div class="staging-actions">
            <!-- Launch Program option -->
            <button 
              v-if="settings.launchMethod === 'program' && settings.launchProgram"
              @click="launchGameProgram" 
              class="btn-action btn-launch">
              🚀 Launch Game
            </button>

            <!-- USB2SNES Upload option (not manual transfer) -->
            <button 
              v-if="settings.launchMethod === 'usb2snes' && settings.usb2snesUploadPref !== 'manual'"
              @click="uploadToUsb2Snes" 
              class="btn-action btn-upload">
              📤 Upload to USB2SNES
            </button>

            <!-- USB2SNES Manual transfer instructions -->
            <div v-if="settings.launchMethod === 'usb2snes' && settings.usb2snesUploadPref === 'manual'" class="manual-upload-instructions">
              <p class="instruction-text">
                📋 Please manually upload the run folder to your USB2SNES device at:<br/>
                <code>{{ settings.usb2snesUploadDir }}</code>
              </p>
              <button @click="manuallyUploadedConfirm" class="btn-action btn-manual-confirm">
                ✓ Manually Uploaded - Launch USB2SNES
              </button>
            </div>
          </div>
        </div>
      </section>
      <footer class="modal-footer">
        <button @click="closeStagingSuccess" class="btn-primary">OK</button>
      </footer>
    </div>
  </div>

  <!-- Quick Launch Progress Modal -->
  <div v-if="quickLaunchProgressModalOpen" class="modal-backdrop">
    <div class="modal staging-progress-modal">
      <header class="modal-header">
        <h3>🎮 Staging Games for Quick Launch...</h3>
      </header>
      <section class="modal-body">
        <div class="progress-info">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: (quickLaunchProgressCurrent / quickLaunchProgressTotal * 100) + '%' }"></div>
          </div>
          <p class="progress-text">{{ quickLaunchProgressCurrent }} / {{ quickLaunchProgressTotal }}</p>
          <p class="progress-game">{{ quickLaunchProgressGameName }}</p>
        </div>
      </section>
    </div>
  </div>

  <!-- Quick Launch Success Modal -->
  <div v-if="quickLaunchSuccessModalOpen" class="modal-backdrop">
    <div class="modal staging-success-modal">
      <header class="modal-header">
        <h3>✅ Games Staged Successfully!</h3>
      </header>
      <section class="modal-body">
        <div class="success-info">
          <p class="success-message">
            <strong>{{ quickLaunchSfcCount }}</strong> game file{{ quickLaunchSfcCount === 1 ? '' : 's' }} {{ quickLaunchSfcCount === 1 ? 'has' : 'have' }} been prepared for quick launch.
          </p>
          <div class="folder-info">
            <label class="folder-label">Staged Games Folder:</label>
            <div class="folder-path">
              <input type="text" readonly :value="quickLaunchFolderPath" class="folder-path-input" />
              <button @click="openQuickLaunchFolder" class="btn-open-folder" title="Open Folder">📁</button>
            </div>
          </div>

          <div class="launch-instructions">
            <h4>🚀 How to Launch:</h4>
            <ol>
              <li>Navigate to the folder above (click the 📁 button)</li>
              <li>Find the game file(s): <code>smw&lt;GAMEID&gt;_&lt;VERSION&gt;.sfc</code></li>
              <li>Load the .sfc file in your preferred emulator or device</li>
              <li>Check the corresponding <code>md&lt;GAMEID&gt;_&lt;VERSION&gt;.json</code> file for game metadata</li>
            </ol>
            <p class="tip">💡 <strong>Tip:</strong> You can configure a launch program in Settings to automatically open games.</p>
          </div>
        </div>
      </section>
      <footer class="modal-footer">
        <button @click="closeQuickLaunchSuccess" class="btn-primary">OK</button>
      </footer>
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted, watch } from 'vue';
import { 
  DEFAULT_THEME, 
  DEFAULT_TEXT_SIZE, 
  applyTheme, 
  applyTextSize,
  getThemeDisplayName,
  getTextSizeDisplayName,
  type ThemeName,
  type TextSize 
} from './themeConfig';

// Debounce utility
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
  let timeout: NodeJS.Timeout | null = null;
  return ((...args: any[]) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  }) as T;
}

type ItemStatus = 'Default' | 'In Progress' | 'Finished';

type Item = {
  Id: string;
  Name: string;
  Type: string;
  LegacyType?: string;
  Author: string;
  Length: string;
  PublicDifficulty?: string;
  Status: ItemStatus;
  MyDifficultyRating?: number | null;  // 0-5
  MyReviewRating?: number | null;      // 0-5
  MySkillRating?: number | null;       // 0-10
  Publicrating?: number;
  Hidden: boolean;
  ExcludeFromRandom?: boolean;
  Mynotes?: string;
  JsonData?: any;
  AvailableVersions?: number[];
  CurrentVersion?: number;
};

// Loading and error states
const isLoading = ref(false);
const loadError = ref<string | null>(null);

// Main data (will be loaded from database)
const items = reactive<Item[]>([]);

const selectedIds = ref<Set<string>>(new Set());
const searchQuery = ref('');
const showHidden = ref(false);
const hideFinished = ref(false);
const bulkStatus = ref('');

// Version management (must be declared before watchers use it)
const selectedVersion = ref<number>(1);

const normalized = (s: string) => s.toLowerCase();

const filteredItems = computed(() => {
  const q = normalized(searchQuery.value.trim());
  return items.filter((it) => {
    if (!showHidden.value && it.Hidden) return false;
    if (hideFinished.value && it.Status === 'Finished') return false;
    if (q.length === 0) return true;
    const haystack = [
      it.Id,
      it.Name,
      it.Type,
      it.Author,
      it.Length,
      it.Status,
      String(it.MyDifficultyRating ?? ''),
      String(it.MyReviewRating ?? ''),
      String(it.Publicrating ?? ''),
      String(it.Mynotes ?? ''),
    ].join(' ').toLowerCase();
    return haystack.includes(q);
  });
});

const hasActiveFilters = computed(() => searchQuery.value.trim().length > 0 || hideFinished.value || showHidden.value);

const numChecked = computed(() => selectedIds.value.size);
const exactlyOneSelected = computed(() => selectedIds.value.size === 1);
const canStartGames = computed(() => selectedIds.value.size >= 1 && selectedIds.value.size <= 21);

const allVisibleChecked = computed(() => {
  if (filteredItems.value.length === 0) return false;
  return filteredItems.value.every((it) => selectedIds.value.has(it.Id));
});

function toggleCheckAll(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.checked) {
    for (const it of filteredItems.value) selectedIds.value.add(it.Id);
  } else {
    for (const it of filteredItems.value) selectedIds.value.delete(it.Id);
  }
}

function rowClick(row: Item) {
  const has = selectedIds.value.has(row.Id);
  selectedIds.value.clear();
  if (!has) selectedIds.value.add(row.Id);
}

function toggleMainSelection(id: string, e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  if (checked) {
    selectedIds.value.add(id);
  } else {
    selectedIds.value.delete(id);
  }
}

function isInRun(gameId: string): boolean {
  return runEntries.some(entry => entry.entryType === 'game' && entry.id === gameId);
}

function addSelectedToRun() {
  const selectedGames = items.filter(item => selectedIds.value.has(item.Id));
  let addedCount = 0;
  
  for (const game of selectedGames) {
    // Skip if already in run
    if (isInRun(game.Id)) continue;
    
    const key = `game-${game.Id}-${Date.now()}-${addedCount}`;
    runEntries.push({
      key,
      id: game.Id,
      entryType: 'game',  // Locked as 'game' type
      name: game.Name,
      stageNumber: '',
      stageName: '',
      count: 1,
      // No filter fields for specific games
      filterDifficulty: '',
      filterType: '',
      filterPattern: '',
      seed: '',
      isLocked: true,  // Mark as locked (can't change type)
      conditions: [],  // Challenge conditions
    });
    addedCount++;
  }
  
  // Uncheck all games after adding
  selectedIds.value.clear();
  
  console.log(`Added ${addedCount} games to run`);
}

function clearFilters() {
  searchQuery.value = '';
  hideFinished.value = false;
  showHidden.value = false;
}

function checkAllVisible() {
  for (const it of filteredItems.value) selectedIds.value.add(it.Id);
}

function uncheckAll() {
  selectedIds.value.clear();
}

function checkRandom() {
  if (filteredItems.value.length === 0) return;
  const randomIndex = Math.floor(Math.random() * filteredItems.value.length);
  const randomItem = filteredItems.value[randomIndex];
  selectedIds.value.clear();
  selectedIds.value.add(randomItem.Id);
}

function hideChecked() {
  for (const it of items) if (selectedIds.value.has(it.Id)) it.Hidden = true;
}

function unhideChecked() {
  for (const it of items) if (selectedIds.value.has(it.Id)) it.Hidden = false;
}

function applyBulkStatus() {
  const status = bulkStatus.value as ItemStatus | '';
  if (!status) return;
  for (const it of items) if (selectedIds.value.has(it.Id)) it.Status = status;
  bulkStatus.value = '';
}

function getSingleSelected(): Item | null {
  if (selectedIds.value.size !== 1) return null;
  const id = Array.from(selectedIds.value)[0];
  return items.find((it) => it.Id === id) ?? null;
}

async function startSelected() {
  // Get selected game IDs
  const selectedGameIds = Array.from(selectedIds.value);
  
  if (selectedGameIds.length === 0 || selectedGameIds.length > 21) {
    alert('Please select between 1 and 21 games to launch.');
    return;
  }
  
  if (!isElectronAvailable()) {
    alert('Quick launch requires Electron environment');
    return;
  }
  
  // Validate settings
  if (!settings.vanillaRomPath || !settings.vanillaRomValid) {
    alert('Please configure a valid vanilla SMW ROM in Settings before staging games.');
    openSettings();
    return;
  }
  
  if (!settings.flipsPath || !settings.flipsValid) {
    alert('Please configure FLIPS executable in Settings before staging games.');
    openSettings();
    return;
  }
  
  try {
    // Show progress modal
    quickLaunchProgressModalOpen.value = true;
    quickLaunchProgressCurrent.value = 0;
    quickLaunchProgressTotal.value = selectedGameIds.length;
    quickLaunchProgressGameName.value = 'Preparing games...';
    
    // Listen for progress updates
    const ipcRenderer = (window as any).electronAPI.ipcRenderer;
    if (ipcRenderer) {
      ipcRenderer.on('quick-launch-progress', (_event: any, data: any) => {
        quickLaunchProgressCurrent.value = data.current;
        quickLaunchProgressTotal.value = data.total;
        quickLaunchProgressGameName.value = data.gameName || 'Processing...';
      });
    }
    
    // Stage games for quick launch
    const stagingResult = await (window as any).electronAPI.stageQuickLaunchGames({
      gameIds: selectedGameIds,
      vanillaRomPath: settings.vanillaRomPath,
      flipsPath: settings.flipsPath,
      tempDirOverride: settings.tempDirOverride || ''
    });
    
    // Clean up progress listener
    if (ipcRenderer) {
      ipcRenderer.removeAllListeners('quick-launch-progress');
    }
    
    // Hide progress modal
    quickLaunchProgressModalOpen.value = false;
    
    console.log('Quick launch staging result:', stagingResult);
    
    if (!stagingResult.success) {
      alert('Failed to stage games: ' + stagingResult.error);
      return;
    }
    
    // Show success modal
    quickLaunchFolderPath.value = stagingResult.folderPath;
    quickLaunchSfcCount.value = stagingResult.gamesStaged;
    quickLaunchSuccessModalOpen.value = true;
    
  } catch (error) {
    console.error('Error staging games for quick launch:', error);
    quickLaunchProgressModalOpen.value = false;
    alert('Error staging games: ' + error.message);
  }
}

function editNotes() {
  const it = getSingleSelected();
  if (!it) return;
  const current = it.Mynotes ?? '';
  const next = window.prompt('Edit notes:', current);
  if (next !== null) it.Mynotes = next;
}

function setMyRating() {
  const it = getSingleSelected();
  if (!it) return;
  const current = it.Myrating ?? '';
  const next = window.prompt('Set My rating (0-5):', String(current));
  if (next === null) return;
  const n = Number(next);
  if (!Number.isNaN(n) && n >= 0 && n <= 5) it.Myrating = n;
}

// Settings modal state and logic
const settingsModalOpen = ref(false);
const settings = reactive({
  theme: DEFAULT_THEME as ThemeName,
  textSize: DEFAULT_TEXT_SIZE as TextSize,
  vanillaRomPath: '',
  vanillaRomValid: false,
  flipsPath: '',
  flipsValid: false,
  asarPath: '',
  asarValid: false,
  uberAsmPath: '',
  uberAsmValid: false,
  launchMethod: 'manual' as 'manual' | 'program' | 'usb2snes',
  launchProgram: '',
  launchProgramArgs: '%file',
  usb2snesAddress: 'ws://localhost:64213',
  usb2snesEnabled: 'no' as 'yes' | 'no',
  usb2snesLaunchPref: 'auto' as 'auto' | 'manual' | 'reset',
  usb2snesUploadPref: 'manual' as 'manual' | 'check' | 'always',
  usb2snesUploadDir: '/work',
  tempDirOverride: '',
  tempDirValid: true,
});

function openSettings() {
  settingsModalOpen.value = true;
}

function closeSettings() {
  settingsModalOpen.value = false;
}

// Text size slider mapping (0-3 to text sizes)
const textSizeOptions: TextSize[] = ['small', 'medium', 'large', 'xlarge'];
const textSizeSliderValue = ref(textSizeOptions.indexOf(settings.textSize));

// Theme change handler
function onThemeChange() {
  applyTheme(settings.theme);
}

// Text size change handler
function onTextSizeChange() {
  settings.textSize = textSizeOptions[textSizeSliderValue.value];
  applyTextSize(settings.textSize);
}

async function saveSettings() {
  console.log('Saving settings:', settings);
  
  if (!isElectronAvailable()) {
    console.warn('Mock mode: Settings not saved (Electron not available)');
    closeSettings();
    return;
  }
  
  // Validate tempDirOverride if set
  if (settings.tempDirOverride && settings.tempDirOverride.trim() !== '') {
    try {
      const validation = await (window as any).electronAPI.validatePath(settings.tempDirOverride);
      if (!validation.exists || !validation.isDirectory) {
        alert('Temporary directory override path does not exist or is not a directory. Please provide a valid path or leave blank.');
        settings.tempDirValid = false;
        return;
      }
      settings.tempDirValid = true;
    } catch (error) {
      alert('Error validating temporary directory path: ' + error.message);
      settings.tempDirValid = false;
      return;
    }
  } else {
    settings.tempDirValid = true;
  }
  
  try {
    // Convert settings to object with string values
    const settingsToSave = {
      theme: settings.theme,
      textSize: settings.textSize,
      vanillaRomPath: settings.vanillaRomPath,
      vanillaRomValid: String(settings.vanillaRomValid),
      flipsPath: settings.flipsPath,
      flipsValid: String(settings.flipsValid),
      asarPath: settings.asarPath,
      asarValid: String(settings.asarValid),
      uberAsmPath: settings.uberAsmPath,
      uberAsmValid: String(settings.uberAsmValid),
      launchMethod: settings.launchMethod,
      launchProgram: settings.launchProgram,
      launchProgramArgs: settings.launchProgramArgs,
      usb2snesAddress: settings.usb2snesAddress,
      usb2snesEnabled: settings.usb2snesEnabled,
      usb2snesLaunchPref: settings.usb2snesLaunchPref,
      usb2snesUploadPref: settings.usb2snesUploadPref,
      usb2snesUploadDir: settings.usb2snesUploadDir,
      tempDirOverride: settings.tempDirOverride,
      tempDirValid: String(settings.tempDirValid),
    };
    
    const result = await (window as any).electronAPI.saveSettings(settingsToSave);
    if (result.success) {
      console.log('Settings saved successfully');
    } else {
      console.error('Failed to save settings:', result.error);
      alert(`Error saving settings: ${result.error}`);
    }
  } catch (error: any) {
    console.error('Error saving settings:', error);
    alert(`Error saving settings: ${error.message}`);
  }
  
  closeSettings();
}

// File import handlers
async function handleRomDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const filePath = files[0].path;
    await validateAndSetRom(filePath);
  }
}

async function browseRomFile() {
  if (!isElectronAvailable()) {
    alert('File selection requires Electron environment');
    return;
  }
  
  try {
    const result = await (window as any).electronAPI.selectFile({
      title: 'Select Vanilla SMW ROM',
      filters: [
        { name: 'SNES ROM Files', extensions: ['sfc', 'smc'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });
    
    if (result.success && result.filePath) {
      await validateAndSetRom(result.filePath);
    }
  } catch (error: any) {
    console.error('Error browsing ROM file:', error);
    alert('Error selecting ROM file: ' + error.message);
  }
}

async function validateAndSetRom(filePath: string) {
  if (!isElectronAvailable()) return;
  
  try {
    const validation = await (window as any).electronAPI.validateRomFile(filePath);
    
    if (validation.valid) {
      settings.vanillaRomPath = filePath;
      settings.vanillaRomValid = true;
      console.log('✓ Valid ROM file set:', filePath);
    } else {
      settings.vanillaRomValid = false;
      alert('Invalid ROM file: ' + validation.error);
    }
  } catch (error: any) {
    console.error('Error validating ROM:', error);
    settings.vanillaRomValid = false;
    alert('Error validating ROM: ' + error.message);
  }
}

async function handleFlipsDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const filePath = files[0].path;
    await validateAndSetFlips(filePath);
  }
}

async function browseFlipsFile() {
  if (!isElectronAvailable()) {
    alert('File selection requires Electron environment');
    return;
  }
  
  try {
    const result = await (window as any).electronAPI.selectFile({
      title: 'Select FLIPS Executable',
      filters: [
        { name: 'Executable Files', extensions: ['exe', '*'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });
    
    if (result.success && result.filePath) {
      await validateAndSetFlips(result.filePath);
    }
  } catch (error: any) {
    console.error('Error browsing FLIPS file:', error);
    alert('Error selecting FLIPS file: ' + error.message);
  }
}

async function validateAndSetFlips(filePath: string) {
  if (!isElectronAvailable()) return;
  
  try {
    const validation = await (window as any).electronAPI.validateFlipsFile(filePath);
    
    if (validation.valid) {
      settings.flipsPath = filePath;
      settings.flipsValid = true;
      console.log('✓ Valid FLIPS file set:', filePath);
    } else {
      settings.flipsValid = false;
      alert('Invalid FLIPS file: ' + validation.error);
    }
  } catch (error: any) {
    console.error('Error validating FLIPS:', error);
    settings.flipsValid = false;
    alert('Error validating FLIPS: ' + error.message);
  }
}

async function handleAsarDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const filePath = files[0].path;
    await validateAndSetAsar(filePath);
  }
}

async function handleLaunchProgramDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const filePath = files[0].path;
    settings.launchProgram = filePath;
    console.log('✓ Launch program path set:', filePath);
  }
}

async function browseAsarFile() {
  if (!isElectronAvailable()) {
    alert('File selection requires Electron environment');
    return;
  }
  
  try {
    const result = await (window as any).electronAPI.selectFile({
      title: 'Select ASAR Executable',
      filters: [
        { name: 'Executable Files', extensions: ['exe', '*'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });
    
    if (result.success && result.filePath) {
      await validateAndSetAsar(result.filePath);
    }
  } catch (error: any) {
    console.error('Error browsing ASAR file:', error);
    alert('Error selecting ASAR file: ' + error.message);
  }
}

async function browseLaunchProgram() {
  if (!isElectronAvailable()) {
    alert('File selection requires Electron environment');
    return;
  }
  
  try {
    const result = await (window as any).electronAPI.selectFile({
      title: 'Select Launch Program',
      filters: [
        { name: 'Executable Files', extensions: ['exe', 'sh', 'bat', 'cmd', '*'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });
    
    if (result.success && result.filePath) {
      settings.launchProgram = result.filePath;
      console.log('✓ Launch program path set:', result.filePath);
    }
  } catch (error: any) {
    console.error('Error browsing launch program:', error);
    alert('Error selecting launch program: ' + error.message);
  }
}

async function validateAndSetAsar(filePath: string) {
  if (!isElectronAvailable()) return;
  
  try {
    const validation = await (window as any).electronAPI.validateAsarFile(filePath);
    
    if (validation.valid) {
      settings.asarPath = filePath;
      settings.asarValid = true;
      console.log('✓ Valid ASAR file set:', filePath);
    } else {
      settings.asarValid = false;
      alert('Invalid ASAR file: ' + validation.error);
    }
  } catch (error: any) {
    console.error('Error validating ASAR:', error);
    settings.asarValid = false;
    alert('Error validating ASAR: ' + error.message);
  }
}

async function handleUberAsmDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const filePath = files[0].path;
    await validateAndSetUberAsm(filePath);
  }
}

async function browseUberAsmFile() {
  if (!isElectronAvailable()) {
    alert('File selection requires Electron environment');
    return;
  }
  
  try {
    const result = await (window as any).electronAPI.selectFile({
      title: 'Select UberASM Executable',
      filters: [
        { name: 'Executable Files', extensions: ['exe', '*'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });
    
    if (result.success && result.filePath) {
      await validateAndSetUberAsm(result.filePath);
    }
  } catch (error: any) {
    console.error('Error browsing UberASM file:', error);
    alert('Error selecting UberASM file: ' + error.message);
  }
}

async function validateAndSetUberAsm(filePath: string) {
  if (!isElectronAvailable()) return;
  
  try {
    const validation = await (window as any).electronAPI.validateUberAsmFile(filePath);
    
    if (validation.valid) {
      settings.uberAsmPath = filePath;
      settings.uberAsmValid = true;
      console.log('✓ Valid UberASM file set:', filePath);
    } else {
      settings.uberAsmValid = false;
      alert('Invalid UberASM file: ' + validation.error);
    }
  } catch (error: any) {
    console.error('Error validating UberASM:', error);
    settings.uberAsmValid = false;
    alert('Error validating UberASM: ' + error.message);
  }
}

// Right-side panels state and helpers
type Stage = {
  key: string; // unique key: `${parentId}-${exitNumber}`
  parentId: string;
  exitNumber: string;
  description: string;
  publicRating?: number;
  myNotes?: string;
  myDifficultyRating?: number | null;
  myReviewRating?: number | null;
};

// Demo stage data per item id
const stagesByItemId = reactive<Record<string, Stage[]>>({
  '11374': [
    { key: '11374-1', parentId: '11374', exitNumber: '1', description: 'Intro stage', publicRating: 4.2, myNotes: '', myDifficultyRating: 3, myReviewRating: 4 },
    { key: '11374-2', parentId: '11374', exitNumber: '2', description: 'Shell level', publicRating: 4.5, myNotes: 'practice', myDifficultyRating: 5, myReviewRating: 5 },
  ],
  '17289': [
    { key: '17289-0x0F', parentId: '17289', exitNumber: '0x0F', description: 'Custom level jump', publicRating: 4.6, myNotes: 'good practice', myDifficultyRating: 5, myReviewRating: 4 },
  ],
  '20091': [],
});

const selectedItem = computed(() => {
  const id = Array.from(selectedIds.value)[0];
  return items.find((it) => it.Id === id) ?? null;
});

const currentStages = computed<Stage[]>(() => {
  if (!selectedItem.value) return [];
  return stagesByItemId[selectedItem.value.Id] ?? [];
});

const selectedStageIds = ref<Set<string>>(new Set());

const allStagesChecked = computed(() => {
  const list = currentStages.value;
  if (list.length === 0) return false;
  return list.every((s) => selectedStageIds.value.has(s.key));
});

function toggleCheckAllStages(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.checked) {
    for (const st of currentStages.value) selectedStageIds.value.add(st.key);
  } else {
    for (const st of currentStages.value) selectedStageIds.value.delete(st.key);
  }
}

function toggleStageSelection(key: string, e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  if (checked) selectedStageIds.value.add(key);
  else selectedStageIds.value.delete(key);
}

function addStagesToRun() {
  const ids = Array.from(selectedStageIds.value.values());
  if (ids.length === 0) return;
  
  let addedCount = 0;
  for (const stageKey of ids) {
    const stage = currentStages.value.find(s => s.key === stageKey);
    if (!stage) continue;
    
    const key = `stage-${stage.key}-${Date.now()}-${addedCount}`;
    runEntries.push({
      key,
      id: stage.parentId,
      entryType: 'stage',  // Locked as 'stage' type
      name: selectedItem.value?.Name || '',
      stageNumber: stage.exitNumber,
      stageName: stage.description,
      count: 1,
      // No filter fields for specific stages
      filterDifficulty: '',
      filterType: '',
      filterPattern: '',
      seed: '',
      isLocked: true,  // Mark as locked (can't change type)
      conditions: [],  // Challenge conditions
    });
    addedCount++;
  }
  
  selectedStageIds.value.clear();
  console.log(`Added ${addedCount} stages to run`);
}

function editStageNotes() {
  const ids = Array.from(selectedStageIds.value.values());
  if (ids.length === 0) return;
  const next = window.prompt('Set notes for selected stages:');
  if (next === null) return;
  for (const st of currentStages.value) if (selectedStageIds.value.has(st.key)) st.myNotes = next;
}

function setStageRating(type: 'difficulty' | 'review') {
  const ids = Array.from(selectedStageIds.value.values());
  if (ids.length === 0) return;
  const label = type === 'difficulty' ? 'Difficulty' : 'Review';
  const next = window.prompt(`Set ${label} rating (1-5) for selected stages:`);
  if (next === null) return;
  const n = Number(next);
  if (Number.isNaN(n) || n < 1 || n > 5) return;
  for (const st of currentStages.value) {
    if (selectedStageIds.value.has(st.key)) {
      if (type === 'difficulty') {
        st.myDifficultyRating = n;
      } else {
        st.myReviewRating = n;
      }
    }
  }
}

// Prepare Run modal state and logic
type ChallengeCondition = 'Hitless' | 'Deathless' | 'No Coins' | 'No Powerups' | 'No Midway';

type RunEntry = {
  key: string;
  id: string;
  entryType: 'game' | 'stage' | 'random_game' | 'random_stage';
  name: string;
  stageNumber?: string;
  stageName?: string;
  count: number;
  filterDifficulty?: '' | 'beginner' | 'intermediate' | 'expert';
  filterType?: '' | 'standard' | 'kaizo' | 'traditional';
  filterPattern?: string;
  seed?: string;
  isLocked?: boolean;  // If true, entry type cannot be changed
  conditions: ChallengeCondition[];  // Challenge conditions for this entry
};

const runModalOpen = ref(false);
const runEntries = reactive<RunEntry[]>([]);
const checkedRun = ref<Set<string>>(new Set());
const globalRunConditions = ref<ChallengeCondition[]>([]);  // Global conditions for entire run

// Run execution state
const currentRunUuid = ref<string | null>(null);
const currentRunStatus = ref<'preparing' | 'active' | 'completed' | 'cancelled'>('preparing');
const currentRunName = ref<string>('');
const currentChallengeIndex = ref<number>(0);
const runStartTime = ref<number | null>(null);
const runElapsedSeconds = ref<number>(0);
const runPauseSeconds = ref<number>(0);
const isRunPaused = ref<boolean>(false);
const runTimerInterval = ref<number | null>(null);

// Challenge results tracking
type ChallengeResult = {
  index: number;
  status: 'pending' | 'success' | 'skipped' | 'ok';
  durationSeconds: number;
  revealedEarly: boolean;
};
const challengeResults = ref<ChallengeResult[]>([]);
const undoStack = ref<ChallengeResult[]>([]);

// Run name input modal
const runNameModalOpen = ref(false);
const runNameInput = ref<string>('My Challenge Run');

// Resume run modal
const resumeRunModalOpen = ref(false);
const resumeRunData = ref<any>(null);

// Staging progress modal
const stagingProgressModalOpen = ref(false);
const stagingProgressCurrent = ref(0);
const stagingProgressTotal = ref(0);
const stagingProgressGameName = ref('');

// Staging success modal
const stagingSuccessModalOpen = ref(false);
const stagingFolderPath = ref('');
const stagingSfcCount = ref(0);

// Quick launch progress modal
const quickLaunchProgressModalOpen = ref(false);
const quickLaunchProgressCurrent = ref(0);
const quickLaunchProgressTotal = ref(0);
const quickLaunchProgressGameName = ref('');

// Quick launch success modal
const quickLaunchSuccessModalOpen = ref(false);
const quickLaunchFolderPath = ref('');
const quickLaunchSfcCount = ref(0);

const allRunChecked = computed(() => runEntries.length > 0 && runEntries.every((e) => checkedRun.value.has(e.key)));
const checkedRunCount = computed(() => checkedRun.value.size);
const isRunSaved = computed(() => currentRunUuid.value !== null && currentRunStatus.value === 'preparing');
const isRunActive = computed(() => currentRunStatus.value === 'active');
const currentChallenge = computed(() => {
  if (!isRunActive.value || currentChallengeIndex.value >= runEntries.length) return null;
  return runEntries[currentChallengeIndex.value];
});
const canUndo = computed(() => undoStack.value.length > 0);

// Watch for current challenge changes to reveal random challenges
watch(currentChallengeIndex, async (newIndex) => {
  if (!isRunActive.value || newIndex >= runEntries.length) return;
  
  const challenge = runEntries[newIndex];
  
  // Check if this is an unrevealed random challenge
  if (challenge.id === '(random)' && challenge.name === '???') {
    await revealCurrentChallenge(false);  // Not revealed early (normal reveal)
  }
});

async function openRunModal() {
  if (!randomFilter.count) randomFilter.count = 1;
  
  // Generate a new seed if not set
  if (!randomFilter.seed && isElectronAvailable()) {
    try {
      const result = await (window as any).electronAPI.generateSeed();
      if (result.success) {
        randomFilter.seed = result.seed;
        console.log(`Generated seed: ${result.seed} (mapping ${result.mapId}, ${result.gameCount} games)`);
      }
    } catch (error) {
      console.error('Error generating seed:', error);
      // Fallback
      randomFilter.seed = 'ERROR-' + Math.random().toString(36).slice(2, 7);
    }
  }
  
  runModalOpen.value = true;
}
function closeRunModal() {
  runModalOpen.value = false;
}
function toggleCheckAllRun(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.checked) {
    for (const e of runEntries) checkedRun.value.add(e.key);
  } else {
    for (const e of runEntries) checkedRun.value.delete(e.key);
  }
}
function checkAllRun() {
  for (const e of runEntries) checkedRun.value.add(e.key);
}
function uncheckAllRun() {
  checkedRun.value.clear();
}
function removeCheckedRun() {
  if (checkedRun.value.size === 0) return;
  const keep = runEntries.filter((e) => !checkedRun.value.has(e.key));
  runEntries.splice(0, runEntries.length, ...keep);
  checkedRun.value.clear();
}

function toggleRunEntrySelection(key: string, e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  if (checked) {
    checkedRun.value.add(key);
  } else {
    checkedRun.value.delete(key);
  }
}

// Row reordering
const draggedIndex = ref<number | null>(null);

function moveRowUp(index: number) {
  if (index === 0) return;
  const temp = runEntries[index];
  runEntries[index] = runEntries[index - 1];
  runEntries[index - 1] = temp;
}

function moveRowDown(index: number) {
  if (index >= runEntries.length - 1) return;
  const temp = runEntries[index];
  runEntries[index] = runEntries[index + 1];
  runEntries[index + 1] = temp;
}

function handleDragStart(index: number, e: DragEvent) {
  draggedIndex.value = index;
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(index));
  }
}

function handleDragOver(index: number, e: DragEvent) {
  e.preventDefault();
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move';
  }
}

function handleDrop(dropIndex: number, e: DragEvent) {
  e.preventDefault();
  if (draggedIndex.value === null || draggedIndex.value === dropIndex) return;
  
  const dragIdx = draggedIndex.value;
  const item = runEntries[dragIdx];
  runEntries.splice(dragIdx, 1);
  runEntries.splice(dropIndex, 0, item);
}

function handleDragEnd() {
  draggedIndex.value = null;
}

// Bulk move operations
const canMoveCheckedUp = computed(() => {
  if (checkedRun.value.size === 0) return false;
  // Can't move up if first item is checked
  const firstCheckedIndex = runEntries.findIndex(e => checkedRun.value.has(e.key));
  return firstCheckedIndex > 0;
});

const canMoveCheckedDown = computed(() => {
  if (checkedRun.value.size === 0) return false;
  // Can't move down if last item is checked
  const lastCheckedIndex = runEntries.map((e, i) => checkedRun.value.has(e.key) ? i : -1)
    .reduce((max, val) => Math.max(max, val), -1);
  return lastCheckedIndex < runEntries.length - 1;
});

function moveCheckedUp() {
  if (!canMoveCheckedUp.value) return;
  
  // Move from top to bottom to preserve relative order
  for (let i = 1; i < runEntries.length; i++) {
    if (checkedRun.value.has(runEntries[i].key) && !checkedRun.value.has(runEntries[i - 1].key)) {
      const temp = runEntries[i];
      runEntries[i] = runEntries[i - 1];
      runEntries[i - 1] = temp;
    }
  }
}

function moveCheckedDown() {
  if (!canMoveCheckedDown.value) return;
  
  // Move from bottom to top to preserve relative order
  for (let i = runEntries.length - 2; i >= 0; i--) {
    if (checkedRun.value.has(runEntries[i].key) && !checkedRun.value.has(runEntries[i + 1].key)) {
      const temp = runEntries[i];
      runEntries[i] = runEntries[i + 1];
      runEntries[i + 1] = temp;
    }
  }
}

const randomFilter = reactive({ type: 'any', difficulty: 'any', pattern: '', count: 1 as number | null, seed: '' });
const isRandomAddValid = computed(() => typeof randomFilter.count === 'number' && randomFilter.count >= 1 && randomFilter.count <= 100);
async function regenerateSeed() {
  if (!isElectronAvailable()) {
    randomFilter.seed = 'MOCK-' + Math.random().toString(36).slice(2, 7);
    return;
  }
  
  try {
    const result = await (window as any).electronAPI.generateSeed();
    if (result.success) {
      randomFilter.seed = result.seed;
      console.log(`Generated seed: ${result.seed} (${result.gameCount} games)`);
    } else {
      alert('Failed to generate seed: ' + result.error);
    }
  } catch (error) {
    console.error('Error generating seed:', error);
    alert('Error generating seed');
  }
}

function addRandomGameToRun() {
  if (!isRandomAddValid.value) return;
  const key = `rand-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const seed = (randomFilter.seed && randomFilter.seed.trim().length > 0)
    ? randomFilter.seed.trim()
    : '';
  
  if (!seed) {
    alert('Seed is required for random challenges. Please wait for seed generation or enter manually.');
    return;
  }
  
  runEntries.push({
    key,
    id: '(random)',
    entryType: 'random_game',  // Default to random_game
    name: 'Random Game',
    stageNumber: '',
    stageName: '',
    count: (randomFilter.count as number) || 1,
    filterDifficulty: randomFilter.difficulty === 'any' ? '' : (randomFilter.difficulty as any),
    filterType: randomFilter.type === 'any' ? '' : (randomFilter.type as any),
    filterPattern: randomFilter.pattern || '',
    seed,
    isLocked: false,  // Can change between random_game and random_stage
    conditions: [],  // Challenge conditions
  });
  
  // Generate new seed for next entry
  regenerateSeed();
}

function stageRun(mode: 'save' | 'upload') {
  console.log('Stage run', mode, runEntries);
  
  // If no name yet, open name input modal
  if (!currentRunName.value) {
    runNameInput.value = 'My Challenge Run';
    runNameModalOpen.value = true;
  } else {
    // Already have name, just save
    saveRunToDatabase();
  }
}

async function saveRunToDatabase() {
  if (!isElectronAvailable()) {
    alert('Run saving requires Electron environment');
    return;
  }
  
  try {
    const runName = currentRunName.value;
    if (!runName) {
      alert('Run name is required');
      return;
    }
    
    // Convert reactive objects to plain objects for IPC
    const plainGlobalConditions = JSON.parse(JSON.stringify(globalRunConditions.value));
    const plainRunEntries = JSON.parse(JSON.stringify(runEntries));
    
    // Create run in database
    const result = await (window as any).electronAPI.createRun(
      runName,
      '',  // runDescription
      plainGlobalConditions
    );
    
    if (!result.success) {
      alert('Failed to create run: ' + result.error);
      return;
    }
    
    // Save run plan
    const planResult = await (window as any).electronAPI.saveRunPlan(
      result.runUuid,
      plainRunEntries
    );
    
    if (!planResult.success) {
      alert('Failed to save run plan: ' + planResult.error);
      return;
    }
    
    currentRunUuid.value = result.runUuid;
    currentRunStatus.value = 'preparing';
    console.log('Run saved with UUID:', result.runUuid);
    
    // Now stage the run (generate SFC files)
    await stageRunGames(result.runUuid, runName);
    
  } catch (error) {
    console.error('Error saving run:', error);
    alert('Error saving run: ' + error.message);
  }
}

async function stageRunGames(runUuid: string, runName: string) {
  try {
    // Show progress modal
    stagingProgressModalOpen.value = true;
    stagingProgressCurrent.value = 0;
    stagingProgressTotal.value = runEntries.length;
    stagingProgressGameName.value = 'Expanding run plan...';
    
    // Step 1: Expand plan and select all random games
    const expandResult = await (window as any).electronAPI.expandAndStageRun({ runUuid });
    
    if (!expandResult.success) {
      stagingProgressModalOpen.value = false;
      alert('Failed to expand run plan: ' + expandResult.error);
      return;
    }
    
    // Listen for progress updates
    const ipcRenderer = (window as any).electronAPI.ipcRenderer;
    if (ipcRenderer) {
      ipcRenderer.on('staging-progress', (_event: any, data: any) => {
        stagingProgressCurrent.value = data.current;
        stagingProgressTotal.value = data.total;
        stagingProgressGameName.value = data.gameName || 'Processing...';
      });
    }
    
    // Step 2: Stage games (create SFC files)
    stagingProgressGameName.value = 'Creating game files...';
    const stagingResult = await (window as any).electronAPI.stageRunGames({
      runUuid,
      vanillaRomPath: settings.vanillaRomPath,
      flipsPath: settings.flipsPath
    });
    
    // Clean up progress listener
    if (ipcRenderer) {
      ipcRenderer.removeAllListeners('staging-progress');
    }
    
    // Hide progress modal
    stagingProgressModalOpen.value = false;
    
    console.log('Staging result:', stagingResult);
    
    if (!stagingResult.success) {
      alert('Failed to stage run games: ' + stagingResult.error);
      return;
    }
    
    // Show success modal
    console.log('Setting folder path:', stagingResult.folderPath);
    console.log('Setting games staged:', stagingResult.gamesStaged);
    stagingFolderPath.value = stagingResult.folderPath;
    stagingSfcCount.value = stagingResult.gamesStaged;
    stagingSuccessModalOpen.value = true;
    
  } catch (error) {
    console.error('Error staging run games:', error);
    stagingProgressModalOpen.value = false;
    alert('Error staging run games: ' + error.message);
  }
}

function confirmRunName() {
  if (!runNameInput.value || runNameInput.value.trim() === '') {
    alert('Please enter a run name');
    return;
  }
  currentRunName.value = runNameInput.value;
  runNameModalOpen.value = false;
  saveRunToDatabase();
}

function cancelRunName() {
  runNameModalOpen.value = false;
}

function closeStagingSuccess() {
  stagingSuccessModalOpen.value = false;
}

function openStagingFolder() {
  if (stagingFolderPath.value) {
    // Use shell to open folder
    const shell = (window as any).electronAPI.shell;
    if (shell && shell.openPath) {
      shell.openPath(stagingFolderPath.value);
    }
  }
}

function closeQuickLaunchSuccess() {
  quickLaunchSuccessModalOpen.value = false;
}

function openQuickLaunchFolder() {
  if (quickLaunchFolderPath.value) {
    // Use shell to open folder
    const shell = (window as any).electronAPI.shell;
    if (shell && shell.openPath) {
      shell.openPath(quickLaunchFolderPath.value);
    }
  }
}

function launchGameProgram() {
  // TODO: Implement launching the configured game program with first SFC file
  alert('Launch game program - to be implemented');
  // This will be implemented in a later phase
}

function uploadToUsb2Snes() {
  // TODO: Implement USB2SNES upload
  alert('USB2SNES upload - to be implemented');
  // This will be implemented in a later phase
}

function manuallyUploadedConfirm() {
  // TODO: Implement USB2SNES launch after manual upload
  alert('USB2SNES launch - to be implemented');
  // This will be implemented in a later phase
}

async function startRun() {
  if (!currentRunUuid.value) {
    alert('No run saved. Please save the run first.');
    return;
  }
  
  if (!isElectronAvailable()) {
    alert('Run execution requires Electron environment');
    return;
  }
  
  const confirmed = confirm(
    `Start run "${currentRunName.value}"?\n\n` +
    `${runEntries.length} plan entries\n` +
    `Global conditions: ${globalRunConditions.value.length > 0 ? globalRunConditions.value.join(', ') : 'None'}\n\n` +
    `Once started, the run cannot be edited.`
  );
  
  if (!confirmed) return;
  
  try {
    const result = await (window as any).electronAPI.startRun({
      runUuid: currentRunUuid.value
    });
    
    if (result.success) {
      // Fetch the expanded run results from database
      const expandedResults = await (window as any).electronAPI.getRunResults({
        runUuid: currentRunUuid.value
      });
      
      if (!expandedResults || expandedResults.length === 0) {
        alert('Failed to load run results');
        return;
      }
      
      // Replace runEntries with expanded results
      runEntries.length = 0;  // Clear array
      expandedResults.forEach((res: any) => {
        // Mask random games that haven't been revealed yet
        const isUnrevealed = res.was_random && !res.revealed_early;
        
        runEntries.push({
          key: res.result_uuid,
          id: isUnrevealed ? '(random)' : (res.gameid || '(random)'),
          entryType: res.was_random ? 'random_game' : 'game',
          name: isUnrevealed ? '???' : (res.game_name || '???'),
          stageNumber: res.exit_number,
          stageName: isUnrevealed ? null : res.stage_description,
          count: 1,  // Each result is now a single challenge
          isLocked: true,  // All entries locked during active run
          conditions: JSON.parse(res.conditions || '[]')
        });
      });
      
      currentRunStatus.value = 'active';
      currentChallengeIndex.value = 0;
      runStartTime.value = Date.now();
      runElapsedSeconds.value = 0;
      
      // Initialize challenge results tracking
      challengeResults.value = runEntries.map((_, idx) => ({
        index: idx,
        status: 'pending',
        durationSeconds: 0,
        revealedEarly: false
      }));
      undoStack.value = [];
      
      // Start timer for first challenge
      if (challengeResults.value.length > 0) {
        challengeResults.value[0].durationSeconds = 0;
      }
      
      // Start timer
      runTimerInterval.value = window.setInterval(() => {
        if (runStartTime.value) {
          runElapsedSeconds.value = Math.floor((Date.now() - runStartTime.value) / 1000);
          // Update current challenge duration
          if (currentChallengeIndex.value < challengeResults.value.length) {
            const current = challengeResults.value[currentChallengeIndex.value];
            if (current.status === 'pending') {
              // Calculate duration since this challenge started
              const prevDuration = challengeResults.value
                .slice(0, currentChallengeIndex.value)
                .reduce((sum, r) => sum + r.durationSeconds, 0);
              current.durationSeconds = runElapsedSeconds.value - prevDuration;
            }
          }
        }
      }, 1000);
      
      console.log(`Run started with ${runEntries.length} challenges`);
      
      // Reveal first challenge if it's random (watcher won't trigger for initial index=0)
      if (runEntries.length > 0) {
        const firstChallenge = runEntries[0];
        if ((firstChallenge.entryType === 'random_game' || firstChallenge.entryType === 'random_stage') && firstChallenge.name === '???') {
          await revealCurrentChallenge(false);
        }
      }
    } else {
      alert('Failed to start run: ' + result.error);
    }
  } catch (error) {
    console.error('Error starting run:', error);
    alert('Error starting run');
  }
}

async function pauseRun() {
  if (!currentRunUuid.value || isRunPaused.value) return;
  
  try {
    if (isElectronAvailable()) {
      await (window as any).electronAPI.pauseRun(currentRunUuid.value);
    }
    
    isRunPaused.value = true;
    console.log('Run paused');
  } catch (error) {
    console.error('Error pausing run:', error);
    alert('Error pausing run');
  }
}

async function unpauseRun() {
  if (!currentRunUuid.value || !isRunPaused.value) return;
  
  try {
    if (isElectronAvailable()) {
      const result = await (window as any).electronAPI.unpauseRun({ runUuid: currentRunUuid.value });
      if (result.success) {
        // Update pause time with the returned value
        runPauseSeconds.value = result.pauseSeconds || 0;
        isRunPaused.value = false;
        console.log('Run unpaused, total pause time:', runPauseSeconds.value);
      }
    }
  } catch (error) {
    console.error('Error unpausing run:', error);
    alert('Error unpausing run');
  }
}

async function cancelRun() {
  const confirmed = confirm(
    `Cancel run "${currentRunName.value}"?\n\n` +
    `This will mark the run as cancelled. You can view it later but cannot continue it.`
  );
  
  if (!confirmed) return;
  
  try {
    if (isElectronAvailable()) {
      await (window as any).electronAPI.cancelRun({
        runUuid: currentRunUuid.value
      });
    }
    
    // Stop timer
    if (runTimerInterval.value) {
      clearInterval(runTimerInterval.value);
      runTimerInterval.value = null;
    }
    
    currentRunStatus.value = 'cancelled';
    console.log('Run cancelled');
    alert('Run cancelled');
    closeRunModal();
  } catch (error) {
    console.error('Error cancelling run:', error);
    alert('Error cancelling run');
  }
}

async function nextChallenge() {
  if (!currentChallenge.value) return;
  
  const idx = currentChallengeIndex.value;
  const result = challengeResults.value[idx];
  
  // Determine status: 'success' if not revealed early, 'ok' if revealed early
  const finalStatus = result.revealedEarly ? 'ok' : 'success';
  
  // Save current state to undo stack
  undoStack.value.push({
    index: idx,
    status: result.status,
    durationSeconds: result.durationSeconds,
    revealedEarly: result.revealedEarly
  });
  
  // Mark as success or ok
  result.status = finalStatus;
  
  try {
    if (isElectronAvailable()) {
      await (window as any).electronAPI.recordChallengeResult({
        runUuid: currentRunUuid.value,
        challengeIndex: idx,
        status: finalStatus
      });
    }
    
    console.log(`Challenge ${idx + 1} completed (${finalStatus})`);
    
    // Move to next challenge
    if (idx < runEntries.length - 1) {
      currentChallengeIndex.value++;
      // Start timing next challenge
      if (idx + 1 < challengeResults.value.length) {
        challengeResults.value[idx + 1].durationSeconds = 0;
      }
    } else {
      // Run completed
      completeRun();
    }
  } catch (error) {
    console.error('Error recording challenge result:', error);
    alert('Error recording result');
  }
}

async function skipChallenge() {
  if (!currentChallenge.value) return;
  
  const idx = currentChallengeIndex.value;
  const entry = runEntries[idx];
  
  // If this is a random challenge, reveal it first (so user sees what they're skipping)
  if ((entry.entryType === 'random_game' || entry.entryType === 'random_stage') && entry.name === '???') {
    await revealCurrentChallenge(false);  // Normal reveal (not early)
  }
  
  const confirmed = confirm(`Skip challenge ${idx + 1}: ${entry.name}?`);
  if (!confirmed) return;
  
  const result = challengeResults.value[idx];
  
  // Save current state to undo stack
  undoStack.value.push({
    index: idx,
    status: result.status,
    durationSeconds: result.durationSeconds,
    revealedEarly: result.revealedEarly
  });
  
  // Mark as skipped
  result.status = 'skipped';
  
  try {
    if (isElectronAvailable()) {
      await (window as any).electronAPI.recordChallengeResult({
        runUuid: currentRunUuid.value,
        challengeIndex: idx,
        status: 'skipped'
      });
    }
    
    console.log(`Challenge ${idx + 1} skipped`);
    
    // Move to next challenge
    if (idx < runEntries.length - 1) {
      currentChallengeIndex.value++;
      // Start timing next challenge
      if (idx + 1 < challengeResults.value.length) {
        challengeResults.value[idx + 1].durationSeconds = 0;
      }
    } else {
      // Run completed
      completeRun();
    }
  } catch (error) {
    console.error('Error recording skip:', error);
    alert('Error recording skip');
  }
}

async function undoChallenge() {
  if (undoStack.value.length === 0) return;
  
  const previousState = undoStack.value.pop()!;
  const idx = previousState.index;
  
  // Before going back, mark any challenges AFTER this point as revealed_early
  // because the user has already seen them
  for (let i = idx + 1; i < challengeResults.value.length; i++) {
    const result = challengeResults.value[i];
    const entry = runEntries[i];
    
    // If it's a random challenge that's been revealed, mark it as revealed early
    if ((entry.entryType === 'random_game' || entry.entryType === 'random_stage') && 
        entry.name !== '???' && 
        result.status !== 'pending') {
      result.revealedEarly = true;
      challengeResults.value[i] = { ...result, revealedEarly: true };
      
      // Update in database
      try {
        if (isElectronAvailable()) {
          await (window as any).electronAPI.markChallengeRevealedEarly({
            runUuid: currentRunUuid.value,
            challengeIndex: i,
            revealedEarly: true
          });
        }
      } catch (error) {
        console.error('Error marking challenge as revealed early:', error);
      }
    }
  }
  
  // Restore previous state
  challengeResults.value[idx] = { ...previousState };
  
  // Go back to that challenge
  currentChallengeIndex.value = idx;
  
  try {
    if (isElectronAvailable()) {
      // Undo the database record
      await (window as any).electronAPI.recordChallengeResult({
        runUuid: currentRunUuid.value,
        challengeIndex: idx,
        status: 'pending'  // Reset to pending
      });
    }
    
    console.log(`Undone: Challenge ${idx + 1} back to pending`);
  } catch (error) {
    console.error('Error undoing challenge:', error);
    alert('Error undoing challenge');
  }
}

async function revealCurrentChallenge(revealedEarly: boolean = false) {
  if (!isElectronAvailable()) return;
  if (!currentChallenge.value) return;
  
  const challenge = currentChallenge.value;
  const idx = currentChallengeIndex.value;
  
  // Only reveal if it's a random challenge that hasn't been revealed
  if (challenge.id !== '(random)' || challenge.name !== '???') {
    return;  // Already revealed or not random
  }
  
  try {
    const result = await (window as any).electronAPI.revealChallenge({
      runUuid: currentRunUuid.value,
      resultUuid: challenge.key,  // result_uuid
      revealedEarly
    });
    
    if (result.success && !result.alreadyRevealed) {
      // Update UI with revealed game
      challenge.id = result.gameid;
      challenge.name = result.gameName;
      
      // Mark as revealed early if skipped/peeked
      if (revealedEarly) {
        challengeResults.value[idx].revealedEarly = true;
      }
      
      console.log(`Revealed challenge ${idx + 1}: ${result.gameName} (${result.gameid})`);
    }
  } catch (error) {
    console.error('Error revealing challenge:', error);
    // Continue anyway - show error but don't block gameplay
  }
}

function completeRun() {
  // Stop timer
  if (runTimerInterval.value) {
    clearInterval(runTimerInterval.value);
    runTimerInterval.value = null;
  }
  
  currentRunStatus.value = 'completed';
  
  alert(
    `Run "${currentRunName.value}" completed!\n\n` +
    `Total time: ${formatTime(runElapsedSeconds.value)}\n` +
    `Challenges: ${runEntries.length}`
  );
  
  closeRunModal();
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  
  if (h > 0) {
    return `${h}h ${m}m ${s}s`;
  } else if (m > 0) {
    return `${m}m ${s}s`;
  } else {
    return `${s}s`;
  }
}

function getChallengeStatusIcon(index: number): string {
  if (index >= challengeResults.value.length) return '';
  const result = challengeResults.value[index];
  
  switch (result.status) {
    case 'success':
      return '✓';  // Green checkmark - Perfect completion
    case 'ok':
      return '⚠';  // Warning triangle - Completed but revealed early
    case 'skipped':
      return '✗';  // Red X - Skipped
    case 'pending':
    default:
      return '';
  }
}

function getChallengeStatusClass(index: number): string {
  if (index >= challengeResults.value.length) return '';
  const result = challengeResults.value[index];
  
  switch (result.status) {
    case 'success':
      return 'status-success';
    case 'ok':
      return 'status-ok';
    case 'skipped':
      return 'status-skipped';
    case 'pending':
    default:
      return '';
  }
}

function getChallengeDuration(index: number): string {
  if (index >= challengeResults.value.length) return '';
  const result = challengeResults.value[index];
  
  // Only show duration for current and completed challenges
  if (index > currentChallengeIndex.value) return '';
  if (result.durationSeconds === 0 && result.status === 'pending') return '';
  
  return formatTime(result.durationSeconds);
}

// Helper: Check if entry is random type
function isRandomEntry(entry: RunEntry): boolean {
  return entry.entryType === 'random_game' || entry.entryType === 'random_stage';
}

// Challenge conditions management
const allConditions: ChallengeCondition[] = [
  'Hitless',
  'Deathless', 
  'No Coins',
  'No Powerups',
  'No Midway'
];

function editConditions(entry: RunEntry) {
  const current = entry.conditions || [];
  const message = 'Select challenge conditions for this entry:\n\n' +
    allConditions.map((c, i) => `${i + 1}. ${c} ${current.includes(c) ? '✓' : ''}`).join('\n') +
    '\n\nEnter numbers to toggle (e.g., "1,3,5" or "all" or "none"):';
  
  const input = window.prompt(message, current.length === 0 ? '' : 'current');
  if (input === null) return;
  
  const inputLower = input.toLowerCase().trim();
  
  if (inputLower === 'none' || inputLower === '') {
    entry.conditions = [];
    return;
  }
  
  if (inputLower === 'all') {
    entry.conditions = [...allConditions];
    return;
  }
  
  // Parse numbers
  const numbers = inputLower.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n) && n >= 1 && n <= allConditions.length);
  if (numbers.length > 0) {
    const newConditions = numbers.map(n => allConditions[n - 1]);
    entry.conditions = [...new Set(newConditions)];  // Remove duplicates
  }
}

function editGlobalConditions() {
  const current = globalRunConditions.value || [];
  const message = 'Select global challenge conditions for entire run:\n\n' +
    allConditions.map((c, i) => `${i + 1}. ${c} ${current.includes(c) ? '✓' : ''}`).join('\n') +
    '\n\nEnter numbers to toggle (e.g., "1,3,5" or "all" or "none"):';
  
  const input = window.prompt(message, current.length === 0 ? '' : 'current');
  if (input === null) return;
  
  const inputLower = input.toLowerCase().trim();
  
  if (inputLower === 'none' || inputLower === '') {
    globalRunConditions.value = [];
    return;
  }
  
  if (inputLower === 'all') {
    globalRunConditions.value = [...allConditions];
    return;
  }
  
  // Parse numbers
  const numbers = inputLower.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n) && n >= 1 && n <= allConditions.length);
  if (numbers.length > 0) {
    const newConditions = numbers.map(n => allConditions[n - 1]);
    globalRunConditions.value = [...new Set(newConditions)];  // Remove duplicates
  }
}

// ===========================================================================
// DATABASE INTEGRATION
// ===========================================================================

/**
 * Check if running in Electron or standalone browser
 */
const isElectronAvailable = () => {
  return typeof (window as any).electronAPI !== 'undefined';
};

/**
 * Get mock data for development mode (Vite only, no Electron)
 */
function getMockGames(): Item[] {
  return [
    { 
      Id: '11374', 
      Name: 'Super Dram World', 
      Type: 'Kaizo: Intermediate', 
      Author: 'Panga', 
      Length: '18 exits', 
      PublicDifficulty: 'Advanced',
      Status: 'Default', 
      MyDifficultyRating: 4, 
      MyReviewRating: 5,
      MySkillRating: 5,
      Publicrating: 4.3, 
      Hidden: false, 
      ExcludeFromRandom: false,
      Mynotes: '',
      AvailableVersions: [1, 2, 3],
      CurrentVersion: 3,
      JsonData: { gameid: '11374', name: 'Super Dram World', version: 3 }
    },
    { 
      Id: '17289', 
      Name: 'Storks, Apes, and Crocodiles', 
      Type: 'Standard', 
      LegacyType: 'Standard: Hard',
      Author: 'Morsel', 
      Length: 'unknown', 
      PublicDifficulty: 'Moderate',
      Status: 'In Progress', 
      MyDifficultyRating: 5, 
      MyReviewRating: 4,
      MySkillRating: 3,
      Publicrating: 4.6, 
      Hidden: false, 
      ExcludeFromRandom: false,
      Mynotes: 'Practice level 0x0F',
      AvailableVersions: [1, 2],
      CurrentVersion: 2,
      JsonData: { gameid: '17289', name: 'Storks, Apes, and Crocodiles', version: 2 }
    },
    { 
      Id: '20091', 
      Name: 'Example Hack', 
      Type: 'Traditional', 
      Author: 'Someone', 
      Length: '5 exits', 
      PublicDifficulty: 'Easy',
      Status: 'Finished', 
      MyDifficultyRating: 2, 
      MyReviewRating: 2,
      MySkillRating: 1,
      Publicrating: 3.8, 
      Hidden: false, 
      ExcludeFromRandom: true,
      Mynotes: '',
      AvailableVersions: [1],
      CurrentVersion: 1,
      JsonData: { gameid: '20091', name: 'Example Hack', version: 1 }
    },
  ];
}

/**
 * Load all games from database
 */
async function loadGames() {
  isLoading.value = true;
  loadError.value = null;
  
  try {
    if (!isElectronAvailable()) {
      // Development mode without Electron - use mock data
      console.warn('Electron not available, using mock data');
      const mockGames = getMockGames();
      items.splice(0, items.length, ...mockGames);
      isLoading.value = false;
      return;
    }
    
    const games = await (window as any).electronAPI.getGames();
    
    // Get available versions for each game
    for (const game of games) {
      try {
        const versions = await (window as any).electronAPI.getVersions(game.Id);
        game.AvailableVersions = versions;
      } catch (error) {
        console.error(`Error getting versions for ${game.Id}:`, error);
        game.AvailableVersions = [game.CurrentVersion];
      }
    }
    
    items.splice(0, items.length, ...games);
    console.log(`Loaded ${games.length} games from database`);
  } catch (error: any) {
    console.error('Failed to load games:', error);
    loadError.value = error.message || 'Failed to load games';
  } finally {
    isLoading.value = false;
  }
}

/**
 * Load stages for currently selected game
 */
async function loadStages(gameid: string) {
  if (!isElectronAvailable()) {
    // Mock stages data
    const mockStages: Record<string, Stage[]> = {
      '11374': [
        { key: '11374-1', parentId: '11374', exitNumber: '1', description: 'Intro stage', publicRating: 4.2, myNotes: '', myDifficultyRating: 3, myReviewRating: 4 },
        { key: '11374-2', parentId: '11374', exitNumber: '2', description: 'Shell level', publicRating: 4.5, myNotes: 'practice', myDifficultyRating: 5, myReviewRating: 5 },
      ],
      '17289': [
        { key: '17289-0x0F', parentId: '17289', exitNumber: '0x0F', description: 'Custom level jump', publicRating: 4.6, myNotes: 'good practice', myDifficultyRating: 5, myReviewRating: 4 },
      ],
    };
    stagesByItemId[gameid] = mockStages[gameid] || [];
    return mockStages[gameid] || [];
  }
  
  try {
    const stages = await (window as any).electronAPI.getStages(gameid);
    stagesByItemId[gameid] = stages;
    return stages;
  } catch (error) {
    console.error(`Error loading stages for ${gameid}:`, error);
    return [];
  }
}

/**
 * Load settings from database
 */
async function loadSettings() {
  if (!isElectronAvailable()) {
    console.warn('Electron not available, using default settings');
    // Apply defaults even in mock mode
    applyTheme(DEFAULT_THEME);
    applyTextSize(DEFAULT_TEXT_SIZE);
    return;
  }
  
  try {
    const savedSettings = await (window as any).electronAPI.getSettings();
    
    // Apply saved settings to reactive state
    if (savedSettings.theme) {
      settings.theme = savedSettings.theme as ThemeName;
      applyTheme(settings.theme);
    } else {
      applyTheme(DEFAULT_THEME);
    }
    
    if (savedSettings.textSize) {
      settings.textSize = savedSettings.textSize as TextSize;
      textSizeSliderValue.value = textSizeOptions.indexOf(settings.textSize);
      applyTextSize(settings.textSize);
    } else {
      applyTextSize(DEFAULT_TEXT_SIZE);
    }
    
    if (savedSettings.vanillaRomPath) settings.vanillaRomPath = savedSettings.vanillaRomPath;
    if (savedSettings.vanillaRomValid) settings.vanillaRomValid = savedSettings.vanillaRomValid === 'true';
    if (savedSettings.flipsPath) settings.flipsPath = savedSettings.flipsPath;
    if (savedSettings.flipsValid) settings.flipsValid = savedSettings.flipsValid === 'true';
    if (savedSettings.asarPath) settings.asarPath = savedSettings.asarPath;
    if (savedSettings.asarValid) settings.asarValid = savedSettings.asarValid === 'true';
    if (savedSettings.uberAsmPath) settings.uberAsmPath = savedSettings.uberAsmPath;
    if (savedSettings.uberAsmValid) settings.uberAsmValid = savedSettings.uberAsmValid === 'true';
    if (savedSettings.launchMethod) settings.launchMethod = savedSettings.launchMethod as any;
    if (savedSettings.launchProgram) settings.launchProgram = savedSettings.launchProgram;
    if (savedSettings.launchProgramArgs) settings.launchProgramArgs = savedSettings.launchProgramArgs;
    if (savedSettings.usb2snesAddress) settings.usb2snesAddress = savedSettings.usb2snesAddress;
    if (savedSettings.usb2snesEnabled) settings.usb2snesEnabled = savedSettings.usb2snesEnabled as any;
    if (savedSettings.usb2snesLaunchPref) settings.usb2snesLaunchPref = savedSettings.usb2snesLaunchPref as any;
    if (savedSettings.usb2snesUploadPref) settings.usb2snesUploadPref = savedSettings.usb2snesUploadPref as any;
    if (savedSettings.usb2snesUploadDir) settings.usb2snesUploadDir = savedSettings.usb2snesUploadDir;
    if (savedSettings.tempDirOverride !== undefined) settings.tempDirOverride = savedSettings.tempDirOverride;
    if (savedSettings.tempDirValid) settings.tempDirValid = savedSettings.tempDirValid === 'true';
    
    console.log('Settings loaded from database');
  } catch (error) {
    console.error('Error loading settings:', error);
  }
}

/**
 * Save annotation to database (debounced)
 */
const debouncedSaveAnnotation = debounce(async (item: Item) => {
  if (!isElectronAvailable()) {
    console.log('Mock mode: Would save annotation for', item.Id);
    return;
  }
  
  try {
    const annotation = {
      gameid: item.Id,
      status: item.Status,
      myDifficultyRating: item.MyDifficultyRating,
      myReviewRating: item.MyReviewRating,
      mySkillRating: item.MySkillRating,
      hidden: item.Hidden,
      excludeFromRandom: item.ExcludeFromRandom,
      mynotes: item.Mynotes
    };
    
    const result = await (window as any).electronAPI.saveAnnotation(annotation);
    if (!result.success) {
      console.error('Failed to save annotation:', result.error);
    }
  } catch (error) {
    console.error('Error saving annotation:', error);
  }
}, 500);

/**
 * Load specific game version
 */
async function loadGameVersion(gameid: string, version: number) {
  if (!isElectronAvailable()) {
    console.log(`Mock mode: Would load game ${gameid} version ${version}`);
    return;
  }
  
  try {
    const game = await (window as any).electronAPI.getGame(gameid, version);
    if (game) {
      // Update the item in the list
      const index = items.findIndex(it => it.Id === gameid);
      if (index >= 0) {
        // Preserve AvailableVersions
        game.AvailableVersions = items[index].AvailableVersions;
        Object.assign(items[index], game);
      }
    }
  } catch (error) {
    console.error(`Error loading game ${gameid} version ${version}:`, error);
  }
}

/**
 * Initialize on mount
 */
onMounted(async () => {
  console.log('=== APP MOUNTED ===');
  console.log('Electron API available:', isElectronAvailable());
  
  // Check for active run first
  if (isElectronAvailable()) {
    try {
      const activeRun = await (window as any).electronAPI.getActiveRun();
      if (activeRun) {
        resumeRunData.value = activeRun;
        resumeRunModalOpen.value = true;
        console.log('Active run found:', activeRun.run_name);
      }
    } catch (error) {
      console.error('Error checking for active run:', error);
    }
  }
  
  console.log('Starting data load...');
  
  try {
    await loadGames();
    console.log('Games loaded, count:', items.length);
  } catch (error) {
    console.error('Error loading games:', error);
  }
  
  try {
    await loadSettings();
    console.log('Settings loaded');
  } catch (error) {
    console.error('Error loading settings:', error);
  }
  
  console.log('=== INITIALIZATION COMPLETE ===');
});

/**
 * Watch for item changes and auto-save
 */
watch(items, () => {
  // Auto-save when items change
  for (const item of items) {
    debouncedSaveAnnotation(item);
  }
}, { deep: true });

/**
 * Watch for version changes
 */
watch(selectedVersion, async (newVersion) => {
  if (selectedItem.value && newVersion) {
    await loadGameVersion(selectedItem.value.Id, newVersion);
  }
});

/**
 * Watch for selected item changes to load stages
 */
watch(selectedItem, async (newItem, oldItem) => {
  if (newItem && newItem.Id !== oldItem?.Id) {
    // Load stages for this game if not already loaded
    if (!stagesByItemId[newItem.Id]) {
      await loadStages(newItem.Id);
    }
    
    // Set selected version to current version
    selectedVersion.value = newItem.CurrentVersion || 1;
  }
});

// Version management computed properties
const availableVersions = computed(() => {
  return selectedItem.value?.AvailableVersions || [1];
});
const latestVersion = computed(() => {
  const versions = availableVersions.value;
  return versions.length > 0 ? Math.max(...versions) : 1;
});
const isVersionSpecific = computed(() => {
  // Check if current selection has version-specific annotations
  // For now, just check if not latest version
  return selectedVersion.value !== latestVersion.value;
});

// Rating display helpers
function formatRatings(difficulty?: number | null, review?: number | null): string {
  const d = difficulty ? `D:${difficulty}` : 'D:—';
  const r = review ? `R:${review}` : 'R:—';
  return `${d} ${r}`;
}

function difficultyLabel(rating?: number | null): string {
  if (rating === null || rating === undefined) return '';
  const labels = ['Super Easy', 'Very Easy', 'Easy', 'Normal', 'Hard', 'Very Hard'];
  return labels[rating] || '';
}

function reviewLabel(rating?: number | null): string {
  if (rating === null || rating === undefined) return '';
  const labels = ['Terrible', 'Not Recommended', 'Below Average', 'Average', 'Good', 'Excellent'];
  return labels[rating] || '';
}

function skillLabel(rating?: number | null): string {
  if (rating === null || rating === undefined) return '';
  const labels = [
    'Observer',      // 0
    'Casual',        // 1
    'Apprentice',    // 2
    'Advanced',      // 3
    'Expert',        // 4
    'Master',        // 5
    'Legend',        // 6
    'Champion',      // 7
    'Deity',         // 8
    'Speedrunner',   // 9
    'Pro Speedrunner' // 10
  ];
  return labels[rating] || '';
}

function skillRatingHoverText(rating: number): string {
  const texts = [
    'I saw someone play Mario',  // 0
    'Casual',                     // 1
    'Apprentice',                 // 2
    'Advanced',                   // 3
    'Expert',                     // 4
    'Master',                     // 5
    'I am one of the greats: Glitchcat7, jaku, shovda, juzcook, Panga, Stew_, Calco, MrMightymouse, Noblet, MitchFlowerPower, GPB, Aurateur, Pmiller, Barb, ThaBeast, DaWildGrim, etc', // 6
    'I beat Hackers Dragon or JUMP, Responsible World 1.0, Casio, and Fruit Dealer RTA', // 7
    'I would consider a second run of those',  // 8
    'I might speed run a few hacks like these', // 9
    'I did speedrun a few hacks of these'       // 10
  ];
  return texts[rating] || '';
}

// JSON Details Modal
const jsonModalOpen = ref(false);
const jsonDetailsContent = computed(() => {
  if (!selectedItem.value) return '';
  return JSON.stringify(selectedItem.value.JsonData || selectedItem.value, null, 2);
});

function viewJsonDetails() {
  jsonModalOpen.value = true;
}

function closeJsonModal() {
  jsonModalOpen.value = false;
}

// Version-specific rating
function setVersionSpecificRating() {
  if (isVersionSpecific.value) {
    alert('This version already has version-specific ratings.');
    return;
  }
  
  const confirmed = confirm(
    `Set ratings specifically for version ${selectedVersion.value}?\n\n` +
    'This will create a separate rating for this version only, ' +
    'overriding the game-wide rating when viewing this version.'
  );
  
  if (confirmed) {
    // In real implementation, this would create a version-specific annotation
    alert(`Version-specific rating enabled for version ${selectedVersion.value}`);
  }
}

// Export/Import Run
async function exportRunToFile() {
  if (!currentRunUuid.value) {
    alert('No run to export. Please save the run first.');
    return;
  }
  
  if (!isElectronAvailable()) {
    alert('Export requires Electron environment');
    return;
  }
  
  try {
    const result = await (window as any).electronAPI.exportRun(currentRunUuid.value);
    
    if (result.success) {
      const exportJson = JSON.stringify(result.data, null, 2);
      const blob = new Blob([exportJson], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `run-${currentRunName.value.replace(/[^a-z0-9]/gi, '_')}-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      console.log('Run exported successfully');
    } else {
      alert('Failed to export run: ' + result.error);
    }
  } catch (error) {
    console.error('Error exporting run:', error);
    alert('Error exporting run');
  }
}

async function importRunFromFile() {
  if (!isElectronAvailable()) {
    alert('Import requires Electron environment');
    return;
  }
  
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const importData = JSON.parse(text);
      
      const result = await (window as any).electronAPI.importRun(importData);
      
      if (result.success) {
        let message = `Run imported successfully!`;
        if (result.warnings && result.warnings.length > 0) {
          message += `\n\nWarnings:\n${result.warnings.join('\n')}`;
        }
        alert(message);
        
        // Close modal and reload (could load the imported run)
        closeRunModal();
      } else {
        alert('Failed to import run: ' + result.error);
      }
    } catch (error) {
      console.error('Error importing run:', error);
      alert('Error importing run: Invalid file or format');
    }
  };
  
  input.click();
}

// Resume run from startup
async function resumeRunFromStartup() {
  if (!resumeRunData.value) {
    console.error('No resume run data available');
    return;
  }
  
  console.log('Resuming run:', resumeRunData.value);
  
  try {
    // Close resume modal first
    resumeRunModalOpen.value = false;
    
    // Load the run
    currentRunUuid.value = resumeRunData.value.run_uuid;
    currentRunName.value = resumeRunData.value.run_name;
    currentRunStatus.value = 'active';
    runPauseSeconds.value = resumeRunData.value.pause_seconds || 0;
    isRunPaused.value = resumeRunData.value.isPaused;
    
    console.log('Loading run results for:', currentRunUuid.value);
    
    // Check if electronAPI exists
    if (!isElectronAvailable()) {
      throw new Error('Electron API not available');
    }
    
    // Fetch expanded results
    const expandedResults = await (window as any).electronAPI.getRunResults({
      runUuid: currentRunUuid.value
    });
    
    console.log('Fetched run results:', expandedResults);
    
    if (!expandedResults || expandedResults.length === 0) {
      // The run is marked as active but has no results - this is a corrupted run
      // Offer to cancel it
      if (confirm('This run appears to be corrupted (no results found). Would you like to cancel it and start fresh?')) {
        try {
          await (window as any).electronAPI.cancelRun({ runUuid: currentRunUuid.value });
          alert('Run cancelled. You can now create a new run.');
          resumeRunModalOpen.value = false;
          return;
        } catch (cancelError) {
          console.error('Error cancelling corrupted run:', cancelError);
          throw new Error('Could not cancel corrupted run. Please contact support.');
        }
      } else {
        resumeRunModalOpen.value = false;
        return;
      }
    }
    
    // Load run entries
    runEntries.length = 0;
    expandedResults.forEach((res: any) => {
      runEntries.push({
        key: res.result_uuid,
        id: res.gameid || '(random)',
        entryType: res.was_random ? 'random_game' : 'game',
        name: res.game_name || '???',
        stageNumber: res.exit_number,
        stageName: res.stage_description,
        count: 1,
        isLocked: true,
        conditions: JSON.parse(res.conditions || '[]')
      });
    });
    
    console.log('Loaded run entries:', runEntries.length);
    
    // Find current challenge index (first pending)
    currentChallengeIndex.value = expandedResults.findIndex((r: any) => r.status === 'pending');
    if (currentChallengeIndex.value === -1) {
      currentChallengeIndex.value = expandedResults.length - 1;  // All complete, show last
    }
    
    console.log('Current challenge index:', currentChallengeIndex.value);
    
    // Initialize challenge results
    challengeResults.value = expandedResults.map((res: any, idx: number) => ({
      index: idx,
      status: res.status || 'pending',
      durationSeconds: res.duration_seconds || 0,
      revealedEarly: res.revealed_early || false
    }));
    
    // Use the original started_at timestamp from database
    const startedAtString = resumeRunData.value.started_at;
    console.log('DEBUG: started_at from DB:', startedAtString);
    console.log('DEBUG: type:', typeof startedAtString);
    
    // Parse the timestamp (SQLite returns UTC strings, need to handle properly)
    const originalStartTime = new Date(startedAtString + 'Z').getTime(); // Add 'Z' to treat as UTC
    const now = Date.now();
    
    console.log('DEBUG: originalStartTime (ms):', originalStartTime);
    console.log('DEBUG: now (ms):', now);
    console.log('DEBUG: difference (ms):', now - originalStartTime);
    
    runStartTime.value = originalStartTime;
    
    // Calculate current elapsed time (don't use pre-calculated value from backend)
    const totalElapsed = Math.floor((now - originalStartTime) / 1000);
    runElapsedSeconds.value = totalElapsed - runPauseSeconds.value;
    
    console.log('Resuming run. Started at:', startedAtString, 
                'Total elapsed:', totalElapsed, 'Pause seconds:', runPauseSeconds.value, 
                'Net active:', runElapsedSeconds.value, 'Is paused:', isRunPaused.value);
    
    // Start timer (will not update if paused)
    console.log('Starting timer');
    runTimerInterval.value = window.setInterval(() => {
      if (runStartTime.value && !isRunPaused.value) {
        // Calculate from original start time
        const now = Date.now();
        const totalElapsed = Math.floor((now - runStartTime.value) / 1000);
        runElapsedSeconds.value = totalElapsed - runPauseSeconds.value;
        
        // Update current challenge duration
        if (currentChallengeIndex.value < challengeResults.value.length) {
          const current = challengeResults.value[currentChallengeIndex.value];
          if (current.status === 'pending') {
            const prevDuration = challengeResults.value
              .slice(0, currentChallengeIndex.value)
              .reduce((sum, r) => sum + r.durationSeconds, 0);
            current.durationSeconds = runElapsedSeconds.value - prevDuration;
          }
        }
      }
    }, 1000);
    
    // Open run modal
    runModalOpen.value = true;
    
    console.log('Run modal opened, resume complete');
  } catch (error) {
    console.error('Error resuming run:', error);
    alert(`Error resuming run: ${error.message}`);
    resumeRunModalOpen.value = false;
  }
}

async function pauseRunFromStartup() {
  if (!resumeRunData.value) return;
  
  resumeRunModalOpen.value = false;
  
  // Load run in paused state
  await resumeRunFromStartup();
  
  // Pause it
  if (currentRunUuid.value) {
    await pauseRun();
  }
}

async function cancelRunFromStartup() {
  if (!resumeRunData.value) return;
  
  const confirmed = confirm(`Cancel run "${resumeRunData.value.run_name}"?`);
  if (!confirmed) {
    resumeRunModalOpen.value = false;
    return;
  }
  
  try {
    if (isElectronAvailable()) {
      await (window as any).electronAPI.cancelRun({
        runUuid: resumeRunData.value.run_uuid
      });
    }
    
    resumeRunModalOpen.value = false;
    console.log('Run cancelled from startup');
  } catch (error) {
    console.error('Error cancelling run:', error);
    alert('Error cancelling run');
  }
}
</script>

<style>
/* Root variables - these will be overridden by theme */
:root {
  /* Default theme colors (Light) */
  --bg-primary: #ffffff;
  --bg-secondary: #fafafa;
  --bg-tertiary: #f3f4f6;
  --bg-hover: #f9fafb;
  --text-primary: #111827;
  --text-secondary: #374151;
  --text-tertiary: #6b7280;
  --border-primary: #e5e7eb;
  --border-secondary: #d1d5db;
  --accent-primary: #3b82f6;
  --accent-hover: #2563eb;
  --button-bg: #f3f4f6;
  --button-text: #111827;
  --button-hover-bg: #e5e7eb;
  --selected-bg: #dbeafe;
  --selected-text: #1e40af;
  --disabled-text: #9ca3af;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  --modal-bg: #ffffff;
  --modal-overlay: rgba(0, 0, 0, 0.4);
  --modal-border: #d1d5db;
  --scrollbar-track: #f3f4f6;
  --scrollbar-thumb: #d1d5db;
  --scrollbar-thumb-hover: #9ca3af;
  
  /* Default text sizes (Medium) */
  --base-font-size: 14px;
  --small-font-size: 12px;
  --medium-font-size: 14px;
  --large-font-size: 16px;
  --input-padding: 6px 8px;
  --button-padding: 6px 10px;
}

html, body, #app { 
  height: 100%; 
  margin: 0;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: var(--base-font-size);
}

/* Custom Scrollbar Styling */
* {
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
}

*::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

*::-webkit-scrollbar-track {
  background: var(--scrollbar-track);
}

*::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 6px;
  border: 2px solid var(--scrollbar-track);
}

*::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}

.layout { 
  display: flex; 
  flex-direction: column; 
  height: 100%; 
  font-family: system-ui, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.toolbar { 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  gap: 12px; 
  padding: 10px; 
  border-bottom: 1px solid var(--border-primary); 
  background: var(--bg-secondary); 
}

.left-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.right-actions { display: flex; align-items: center; gap: 8px; }
.search { 
  min-width: 240px; 
  padding: var(--input-padding);
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-secondary);
}
.status-setter select { 
  margin-left: 6px;
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-secondary);
}
.toggle { 
  display: inline-flex; 
  align-items: center; 
  gap: 6px; 
  margin-left: 8px;
  color: var(--text-primary);
}

.content { flex: 1; display: flex; min-height: 0; }
.table-wrapper { flex: 1; overflow: auto; background: var(--bg-primary); }
.sidebar { 
  width: 360px; 
  border-left: 1px solid var(--border-primary); 
  padding: 10px; 
  display: flex; 
  flex-direction: column; 
  gap: 10px; 
  overflow: auto; 
  background: var(--bg-primary); 
}
.panel { 
  border: 1px solid var(--border-primary); 
  border-radius: 6px; 
  background: var(--bg-secondary); 
}
.panel > h3 { 
  margin: 0; 
  padding: 8px 10px; 
  border-bottom: 1px solid var(--border-primary); 
  font-size: var(--medium-font-size);
  color: var(--text-primary);
}
.panel-body { 
  padding: 10px;
  color: var(--text-primary);
}
.panel-actions { 
  display: flex; 
  gap: 8px; 
  padding: 8px 10px; 
  border-bottom: 1px solid var(--border-primary); 
  background: var(--bg-hover); 
}
.kv-table { width: 100%; border-collapse: collapse; }
.kv-table th { 
  text-align: left; 
  width: 110px; 
  vertical-align: top; 
  padding: 6px; 
  color: var(--text-secondary); 
}
.kv-table td { 
  padding: 6px;
  color: var(--text-primary);
}
.kv-table input[type="text"], .kv-table input[type="number"], .kv-table textarea, .kv-table select { 
  width: 100%; 
  box-sizing: border-box; 
  padding: var(--input-padding);
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-secondary);
}
.data-table { 
  width: 100%; 
  border-collapse: collapse; 
  font-size: var(--base-font-size); 
}
.data-table thead th { 
  position: sticky; 
  top: 0; 
  background: var(--bg-tertiary); 
  z-index: 10; 
  text-align: left; 
  padding: 8px; 
  border-bottom: 1px solid var(--border-primary);
  color: var(--text-primary);
}
.data-table tbody td { 
  padding: 8px; 
  border-bottom: 1px solid var(--border-primary); 
  vertical-align: top;
  color: var(--text-primary);
}
.data-table tbody tr:hover { background: var(--bg-hover); }
.data-table .col-check { width: 36px; text-align: center; }
.data-table .action { width: 40px; text-align: center; font-weight: bold; }
.data-table .name { font-weight: 600; color: var(--text-primary); }
.data-table .name.in-run { font-weight: 700; }
.data-table .notes { color: var(--text-secondary); }
.data-table tbody tr.hidden { opacity: 0.6; }
.data-table tbody tr.finished .name { text-decoration: line-through; color: var(--text-tertiary); }
.empty { text-align: center; color: var(--text-tertiary); padding: 16px; }

button { 
  padding: var(--button-padding);
  background: var(--button-bg);
  color: var(--button-text);
  border: 1px solid var(--border-secondary);
  border-radius: 4px;
  cursor: pointer;
  font-size: var(--base-font-size);
}

button:hover:not(:disabled) {
  background: var(--button-hover-bg);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal */
.modal-backdrop { 
  position: fixed; 
  inset: 0; 
  background: var(--modal-overlay); 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  z-index: 1000; 
}
.modal { 
  width: 1200px; 
  max-width: 98vw; 
  max-height: 90vh; 
  background: var(--modal-bg); 
  border-radius: 8px; 
  border: 2px solid var(--modal-border);
  overflow: hidden; 
  display: flex; 
  flex-direction: column; 
}
.modal-header { 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  gap: 8px; 
  padding: 10px; 
  background: var(--bg-tertiary); 
  border-bottom: 1px solid var(--border-primary);
  color: var(--text-primary);
}
.modal-header-actions { display: flex; gap: 8px; align-items: center; }
.modal-header .close { font-size: 16px; }
.modal-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding: 10px; border-bottom: 1px solid #e5e7eb; flex-wrap: wrap; }
.modal-toolbar .add-random { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.modal-toolbar .add-random > * { flex: 0 0 auto; }
.modal-toolbar label { display: inline-flex; align-items: center; gap: 6px; }
.modal-toolbar .pattern { min-width: 220px; padding: 6px 8px; }
.modal-toolbar .count { width: 80px; padding: 6px 8px; }
.modal-toolbar .seed { min-width: 160px; padding: 6px 8px; }
.modal-body { padding: 0; overflow: auto; }

/* Column sizing in modal table */
.data-table th.col-seq, .data-table td.col-seq { width: 40px; text-align: center; font-weight: bold; color: #6b7280; }
.data-table th.col-actions, .data-table td.col-actions { width: 70px; text-align: center; }
.data-table th.col-count, .data-table td.col-count { width: 72px; }
.data-table th.col-seed, .data-table td.col-seed { width: 100px; }
.data-table th.col-pattern, .data-table td.col-pattern { width: 220px; }
.data-table td.col-count input { width: 60px; }
.data-table td.col-seed input { width: 90px; }
.data-table td.col-pattern input { width: 200px; }

/* Row reordering */
.btn-mini { padding: 2px 6px; font-size: 12px; margin: 0 2px; }
.data-table tbody tr[draggable="true"] { cursor: move; }
.data-table tbody tr.dragging { opacity: 0.5; background: #e0e7ff; }

/* Run execution */
.btn-start-run { background: #10b981; color: white; font-weight: bold; }
.btn-start-run:hover:not(:disabled) { background: #059669; }
.btn-start-run:disabled { background: #d1d5db; color: #9ca3af; cursor: not-allowed; }
.btn-cancel-run { background: #ef4444; color: white; }
.btn-cancel-run:hover { background: #dc2626; }
.btn-back { background: #6b7280; color: white; }
.btn-back:hover:not(:disabled) { background: #4b5563; }
.btn-back:disabled { background: #d1d5db; color: #9ca3af; cursor: not-allowed; }
.btn-next { background: #10b981; color: white; }
.btn-next:hover:not(:disabled) { background: #059669; }
.btn-skip { background: #f59e0b; color: white; }
.btn-skip:hover:not(:disabled) { background: #d97706; }
.btn-pause { background: #6b7280; color: white; }
.btn-pause:hover { background: #4b5563; }
.btn-unpause { background: #10b981; color: white; font-weight: bold; }
.btn-unpause:hover { background: #059669; }
.run-timer { font-weight: bold; color: #059669; font-size: 16px; padding: 0 8px; }
.pause-time { font-weight: bold; color: #ef4444; font-size: 16px; padding: 0 8px; }
.run-progress { color: #6b7280; padding: 0 8px; }
.data-table tbody tr.current-challenge { background: #dbeafe !important; border-left: 4px solid #3b82f6; font-weight: 600; }
.data-table tbody tr.current-challenge td { background: #dbeafe; }

/* Challenge status */
.col-status { width: 50px; text-align: center; font-size: 20px; }
.col-duration { width: 80px; text-align: right; font-family: monospace; }
.status-icon { font-weight: bold; }
.status-success .status-icon { color: #10b981; }  /* Green checkmark */
.status-ok .status-icon { color: #f59e0b; }  /* Orange warning - revealed early */
.status-skipped .status-icon { color: #ef4444; }  /* Red X */

/* Settings Modal */
.settings-modal { width: 800px; max-width: 95vw; }
.settings-body { 
  padding: 20px; 
  max-height: 70vh; 
  overflow-y: auto;
  background: var(--modal-bg);
}
.settings-section { 
  margin-bottom: 24px; 
  padding-bottom: 16px; 
  border-bottom: 1px solid var(--border-primary); 
}
.settings-section:last-child { border-bottom: none; }
.setting-row { 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  gap: 16px; 
  margin-bottom: 8px; 
}
.setting-label { 
  flex: 0 0 280px; 
  font-weight: 500; 
  display: flex; 
  align-items: center; 
  gap: 8px;
  color: var(--text-primary);
}
.status-icon { color: var(--success-color); font-weight: bold; font-size: 18px; width: 20px; }
.setting-control { flex: 1; display: flex; gap: 8px; align-items: center; }
.setting-control input[type="text"], .setting-control select { 
  flex: 1; 
  padding: var(--input-padding); 
  border: 1px solid var(--border-secondary); 
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
}
.setting-caption { 
  font-size: var(--small-font-size); 
  color: var(--text-tertiary); 
  margin-top: 4px; 
  margin-left: 300px; 
  line-height: 1.5; 
}
.setting-caption.warning { color: var(--warning-color); }
.setting-caption code { 
  background: var(--bg-tertiary); 
  padding: 2px 4px; 
  border-radius: 2px; 
  font-size: 11px;
  color: var(--text-secondary);
}
.setting-caption a { color: var(--accent-primary); text-decoration: none; }
.setting-caption a:hover { text-decoration: underline; }
.setting-current-path { 
  font-size: var(--small-font-size); 
  color: var(--success-color); 
  margin-top: 4px; 
  margin-left: 300px; 
  font-weight: 500; 
}
.setting-current-path code { 
  background: var(--bg-tertiary); 
  padding: 2px 6px; 
  border-radius: 2px; 
  font-size: 11px; 
  color: var(--text-secondary); 
  word-break: break-all; 
}
.drop-zone { 
  flex: 1; 
  border: 2px dashed var(--border-secondary); 
  border-radius: 4px; 
  padding: 12px; 
  text-align: center; 
  color: var(--text-tertiary); 
  background: var(--bg-hover); 
  cursor: pointer; 
  transition: all 0.2s; 
}
.drop-zone:hover { 
  border-color: var(--accent-primary); 
  background: var(--bg-tertiary); 
  color: var(--accent-primary); 
}
.modal-footer { 
  padding: 12px 20px; 
  border-top: 1px solid var(--border-primary); 
  display: flex; 
  justify-content: flex-end; 
  gap: 8px; 
  background: var(--bg-hover); 
}
.btn-primary { 
  padding: 8px 16px; 
  background: var(--accent-primary); 
  color: white; 
  border: none; 
  border-radius: 4px; 
  font-weight: 500; 
  cursor: pointer; 
}
.btn-primary:hover { background: var(--accent-hover); }

/* Text Size Slider */
.text-size-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--bg-tertiary);
  border-radius: 3px;
  outline: none;
}

.text-size-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--accent-primary);
  border-radius: 50%;
  cursor: pointer;
}

.text-size-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--accent-primary);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.text-size-slider:hover::-webkit-slider-thumb {
  background: var(--accent-hover);
}

.text-size-slider:hover::-moz-range-thumb {
  background: var(--accent-hover);
}

.text-size-label {
  min-width: 100px;
  text-align: right;
  font-weight: 500;
  color: var(--text-primary);
}

/* Run Name Modal */
.run-name-modal { width: 500px; max-width: 95vw; }
.run-name-body { padding: 20px; }
.run-name-body label { display: block; font-weight: 600; margin-bottom: 8px; color: #374151; }
.run-name-body input[type="text"] { width: 100%; padding: 10px 12px; font-size: 16px; border: 1px solid #d1d5db; border-radius: 4px; box-sizing: border-box; }
.run-name-body input[type="text"]:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }

/* Resume Run Modal */
.resume-run-modal { width: 600px; max-width: 95vw; }
.resume-run-body { padding: 24px; }
.resume-message { font-size: 16px; margin-bottom: 16px; color: #374151; }
.resume-prompt { font-size: 16px; margin-top: 20px; margin-bottom: 0; font-weight: 600; color: #374151; }
.run-info { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px; margin: 16px 0; }
.run-info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }
.run-info-row:last-child { border-bottom: none; }
.run-info-row .label { font-weight: 600; color: #6b7280; }
.run-info-row .value { font-weight: 500; color: #111827; }
.resume-run-footer { display: flex; gap: 12px; justify-content: center; }
.btn-large { padding: 12px 24px; font-size: 16px; font-weight: 600; }
.btn-secondary { background: #6b7280; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-secondary:hover { background: #4b5563; }
.btn-danger { background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-danger:hover { background: #dc2626; }

/* Staging Progress Modal */
.staging-progress-modal { width: 500px; max-width: 90vw; }
.progress-info { padding: 24px; }
.progress-bar { 
  width: 100%; 
  height: 30px; 
  background: #e5e7eb; 
  border-radius: 15px; 
  overflow: hidden;
  margin-bottom: 16px;
}
.progress-fill { 
  height: 100%; 
  background: linear-gradient(90deg, #3b82f6, #2563eb); 
  transition: width 0.3s ease;
}
.progress-text { 
  text-align: center; 
  font-size: 18px; 
  font-weight: 600; 
  color: #1f2937;
  margin: 8px 0;
}
.progress-game { 
  text-align: center; 
  font-size: 14px; 
  color: #6b7280;
  margin: 8px 0;
  min-height: 20px;
}

/* Staging Success Modal */
.staging-success-modal { width: 700px; max-width: 95vw; }
.success-info { padding: 24px; }
.success-message { 
  font-size: 18px; 
  margin-bottom: 24px; 
  text-align: center;
  color: #059669;
  font-weight: 600;
}
.folder-info { 
  margin: 24px 0; 
  padding: 16px;
  background: #f0f9ff;
  border: 2px solid #0ea5e9;
  border-radius: 8px;
}
.folder-label { 
  display: block; 
  font-weight: 700; 
  margin-bottom: 10px; 
  color: #0c4a6e;
  font-size: 15px;
}
.folder-path { 
  display: flex; 
  gap: 8px; 
  align-items: center;
}
.folder-path-input { 
  flex: 1; 
  padding: 10px 14px; 
  border: 2px solid #0ea5e9; 
  border-radius: 6px;
  background: white;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
  color: #0c4a6e;
  cursor: text;
  user-select: all;
}
.folder-path-input:focus {
  outline: none;
  border-color: #0284c7;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}
.btn-open-folder { 
  padding: 10px 18px; 
  background: #0ea5e9; 
  color: white; 
  border: none; 
  border-radius: 6px;
  cursor: pointer;
  font-size: 20px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.btn-open-folder:hover { 
  background: #0284c7;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.15);
}
.btn-open-folder:active {
  transform: translateY(0);
}
.staging-actions { 
  margin-top: 24px; 
  display: flex; 
  flex-direction: column;
  gap: 12px;
  align-items: center;
}
.btn-action { 
  padding: 12px 24px; 
  font-size: 16px; 
  font-weight: 600;
  border: none; 
  border-radius: 6px;
  cursor: pointer;
  min-width: 200px;
}
.btn-launch { 
  background: #10b981; 
  color: white;
}
.btn-launch:hover { background: #059669; }
.btn-upload { 
  background: #8b5cf6; 
  color: white;
}
.btn-upload:hover { background: #7c3aed; }
.btn-manual-confirm { 
  background: #f59e0b; 
  color: white;
  margin-top: 12px;
}
.btn-manual-confirm:hover { background: #d97706; }
.manual-upload-instructions { 
  background: #fef3c7; 
  border: 2px solid #fbbf24;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  width: 100%;
}
.instruction-text { 
  margin: 0 0 12px 0; 
  color: #92400e;
  line-height: 1.6;
}
.instruction-text code { 
  background: #fef3c7; 
  padding: 2px 6px; 
  border-radius: 3px;
  font-weight: 600;
  color: #92400e;
}

.launch-instructions {
  margin-top: 20px;
  padding: 16px;
  background: #f3f4f6;
  border-radius: 8px;
}

.launch-instructions h4 {
  margin: 0 0 12px 0;
  color: #374151;
  font-size: 16px;
}

.launch-instructions ol {
  margin: 0 0 12px 0;
  padding-left: 24px;
  color: #4b5563;
  line-height: 1.8;
}

.launch-instructions li {
  margin-bottom: 8px;
}

.launch-instructions code {
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 600;
  color: #1f2937;
  font-size: 0.9em;
}

.launch-instructions .tip {
  margin: 12px 0 0 0;
  padding: 12px;
  background: #dbeafe;
  border-left: 4px solid #3b82f6;
  border-radius: 4px;
  color: #1e40af;
  font-size: 14px;
}

.launch-instructions .tip strong {
  font-weight: 600;
}

/* New UI Components */

/* Read-only fields */
.readonly-field { 
  color: #374151; 
  background: #f9fafb; 
  padding: 6px 8px; 
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

/* Star rating component */
.star-rating { 
  display: flex; 
  align-items: center; 
  gap: 4px; 
}

.star { 
  font-size: 24px; 
  cursor: pointer; 
  color: #d1d5db; 
  user-select: none;
  transition: all 0.2s;
}

.star:hover { 
  color: #fbbf24;
  transform: scale(1.1);
}

.star.filled { 
  color: #f59e0b;
}

.btn-clear-rating {
  padding: 2px 6px;
  font-size: 12px;
  margin-left: 4px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  cursor: pointer;
}

.btn-clear-rating:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

.rating-label {
  margin-left: 8px;
  font-size: 13px;
  color: #6b7280;
  font-style: italic;
  min-width: 100px;
}

/* Detail action buttons */
.detail-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-actions button {
  flex: 1;
  min-width: 150px;
  padding: 6px 10px;
  font-size: 13px;
}

/* JSON Modal */
.json-modal {
  width: 900px;
  max-width: 95vw;
}

.json-body {
  padding: 20px;
  max-height: 70vh;
  overflow: auto;
  background: #1f2937;
}

.json-body pre {
  margin: 0;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #e5e7eb;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Skill Rating (smaller stars for 0-10 scale) */
.star-small {
  font-size: 18px;
}

/* Conditions column */
.col-conditions {
  width: 80px;
  text-align: center;
}

.btn-conditions {
  padding: 4px 8px;
  font-size: 11px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-conditions:hover {
  background: #e0e7ff;
  border-color: #818cf8;
}

.btn-conditions-header {
  padding: 6px 10px;
  font-size: 12px;
  background: #eff6ff;
  border: 1px solid #93c5fd;
  border-radius: 4px;
  cursor: pointer;
}

.btn-conditions-header:hover {
  background: #dbeafe;
  border-color: #60a5fa;
}

/* Skill rating caption */
.skill-rating-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-caption {
  font-size: 12px;
  color: #059669;
  font-style: italic;
  line-height: 1.4;
  padding: 6px 8px;
  background: #f0fdf4;
  border-left: 3px solid #10b981;
  border-radius: 3px;
}

/* Loading overlay */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 100;
  font-size: 16px;
  color: #374151;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 12px 16px;
  margin: 16px;
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  color: #991b1b;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.error-message button {
  background: #dc2626;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.error-message button:hover {
  background: #b91c1c;
}
</style>

