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
        <button @click="startSelected" :disabled="!exactlyOneSelected">Start</button>
        <button @click="editNotes" :disabled="!exactlyOneSelected">Edit notes</button>
        <button @click="setMyRating" :disabled="!exactlyOneSelected">My rating</button>
      </div>
    </header>

    <section class="content">
      <div class="table-wrapper">
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
                  <th>My Skill Rating</th>
                  <td>
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
        <h3>Prepare Run</h3>
        <div class="modal-header-actions">
          <button @click="editGlobalConditions" class="btn-conditions-header" :title="`Global Conditions: ${globalRunConditions.length > 0 ? globalRunConditions.join(', ') : 'None'}`">
            {{ globalRunConditions.length > 0 ? `✓ Global Conditions (${globalRunConditions.length})` : 'Set Global Conditions' }}
          </button>
          <button @click="stageRun('save')" :disabled="runEntries.length === 0">Stage and Save</button>
          <button @click="stageRun('upload')" :disabled="runEntries.length === 0">Stage and Upload</button>
          <button class="close" @click="closeRunModal">✕</button>
        </div>
      </header>

      <section class="modal-toolbar">
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
            <input class="seed" v-model="randomFilter.seed" type="text" placeholder="(random by default)" />
          </label>
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
                draggable="true"
                @dragstart="handleDragStart(idx, $event)"
                @dragover.prevent="handleDragOver(idx, $event)"
                @drop="handleDrop(idx, $event)"
                @dragend="handleDragEnd"
                :class="{ 'dragging': draggedIndex === idx }"
              >
                <td class="col-check">
                  <input type="checkbox" :checked="checkedRun.has(entry.key)" @change="toggleRunEntrySelection(entry.key, $event)" />
                </td>
                <td class="col-seq">{{ idx + 1 }}</td>
                <td class="col-actions">
                  <button class="btn-mini" @click="moveRowUp(idx)" :disabled="idx === 0" title="Move up">↑</button>
                  <button class="btn-mini" @click="moveRowDown(idx)" :disabled="idx === runEntries.length - 1" title="Move down">↓</button>
                </td>
                <td>{{ entry.id }}</td>
                <td>
                  <select v-model="entry.entryType" :disabled="entry.isLocked">
                    <option value="game" v-if="entry.isLocked && entry.entryType === 'game'">Game</option>
                    <option value="stage" v-if="entry.isLocked && entry.entryType === 'stage'">Stage</option>
                    <option value="random_game" v-if="!entry.isLocked || entry.entryType === 'random_game'">Random Game</option>
                    <option value="random_stage" v-if="!entry.isLocked || entry.entryType === 'random_stage'">Random Stage</option>
                  </select>
                </td>
                <td>{{ entry.name }}</td>
                <td>{{ entry.stageNumber ?? '' }}</td>
                <td>{{ entry.stageName ?? '' }}</td>
                <td class="col-count"><input type="number" min="1" v-model.number="entry.count" /></td>
                <td v-if="isRandomEntry(entry)">
                  <select v-model="entry.filterDifficulty">
                    <option value="">—</option>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="expert">Expert</option>
                  </select>
                </td>
                <td v-else>—</td>
                <td v-if="isRandomEntry(entry)">
                  <select v-model="entry.filterType">
                    <option value="">—</option>
                    <option value="standard">Standard</option>
                    <option value="kaizo">Kaizo</option>
                    <option value="traditional">Traditional</option>
                  </select>
                </td>
                <td v-else>—</td>
                <td class="col-pattern" v-if="isRandomEntry(entry)"><input v-model="entry.filterPattern" /></td>
                <td class="col-pattern" v-else>—</td>
                <td class="col-seed" v-if="isRandomEntry(entry)"><input v-model="entry.seed" /></td>
                <td class="col-seed" v-else>—</td>
                <td class="col-conditions">
                  <button @click="editConditions(entry)" class="btn-mini btn-conditions" :title="`Conditions: ${entry.conditions.length > 0 ? entry.conditions.join(', ') : 'None'}`">
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
              <input type="text" v-model="settings.launchProgram" placeholder="Path to launch program" />
            </div>
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
          <div class="setting-caption">
            Download UberASM from <a href="https://smwc.me/s/39036" target="_blank">https://smwc.me/s/39036</a>
          </div>
        </div>
      </section>

      <footer class="modal-footer">
        <button @click="saveSettings" class="btn-primary">Save Changes and Close</button>
      </footer>
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

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

const items = reactive<Item[]>([
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
    MySkillRating: 5,  // Master level when rated
    Publicrating: 4.3, 
    Hidden: false, 
    ExcludeFromRandom: false,
    Mynotes: '',
    AvailableVersions: [1, 2, 3],
    CurrentVersion: 3,
    JsonData: { gameid: '11374', name: 'Super Dram World', version: 3, author: 'Panga', difficulty: 'Advanced' }
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
    MySkillRating: 3,  // Advanced when rated
    Publicrating: 4.6, 
    Hidden: false, 
    ExcludeFromRandom: false,
    Mynotes: 'Practice level 0x0F',
    AvailableVersions: [1, 2],
    CurrentVersion: 2,
    JsonData: { gameid: '17289', name: 'Storks, Apes, and Crocodiles', version: 2, author: 'Morsel' }
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
    MySkillRating: 1,  // Casual when rated
    Publicrating: 3.8, 
    Hidden: false, 
    ExcludeFromRandom: true,
    Mynotes: '',
    AvailableVersions: [1],
    CurrentVersion: 1,
    JsonData: { gameid: '20091', name: 'Example Hack', version: 1, author: 'Someone' }
  },
]);

const selectedIds = ref<Set<string>>(new Set());
const searchQuery = ref('');
const showHidden = ref(false);
const hideFinished = ref(false);
const bulkStatus = ref('');

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

function startSelected() {
  const it = getSingleSelected();
  if (!it) return;
  // Replace with actual start logic when integrated
  console.log('Start item', it.Id, it.Name);
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
  vanillaRomValid: false,
  flipsValid: false,
  asarValid: false,
  uberAsmValid: false,
  launchMethod: 'manual' as 'manual' | 'program' | 'usb2snes',
  launchProgram: '',
  launchProgramArgs: '%file',
  usb2snesAddress: 'ws://localhost:64213',
  usb2snesEnabled: 'no' as 'yes' | 'no',
  usb2snesLaunchPref: 'auto' as 'auto' | 'manual' | 'reset',
  usb2snesUploadPref: 'manual' as 'manual' | 'check' | 'always',
  usb2snesUploadDir: '/work',
});

function openSettings() {
  settingsModalOpen.value = true;
}

function closeSettings() {
  settingsModalOpen.value = false;
}

function saveSettings() {
  console.log('Saving settings:', settings);
  // TODO: Persist settings via IPC
  closeSettings();
}

// File import handlers (placeholders for IPC integration)
function handleRomDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    console.log('ROM file dropped:', files[0].name);
    // TODO: Validate and import via IPC
  }
}

function browseRomFile() {
  console.log('Browse ROM file');
  // TODO: Open file picker via IPC
}

function handleFlipsDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    console.log('FLIPS file dropped:', files[0].name);
    // TODO: Import via IPC
  }
}

function browseFlipsFile() {
  console.log('Browse FLIPS file');
  // TODO: Open file picker via IPC
}

function handleAsarDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    console.log('ASAR file dropped:', files[0].name);
    // TODO: Import via IPC
  }
}

function browseAsarFile() {
  console.log('Browse ASAR file');
  // TODO: Open file picker via IPC
}

function handleUberAsmDrop(e: DragEvent) {
  e.preventDefault();
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    console.log('UberASM file dropped:', files[0].name);
    // TODO: Import via IPC
  }
}

function browseUberAsmFile() {
  console.log('Browse UberASM file');
  // TODO: Open file picker via IPC
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

const allRunChecked = computed(() => runEntries.length > 0 && runEntries.every((e) => checkedRun.value.has(e.key)));
const checkedRunCount = computed(() => checkedRun.value.size);

function openRunModal() {
  if (!randomFilter.seed) randomFilter.seed = Math.random().toString(36).slice(2, 10);
  if (!randomFilter.count) randomFilter.count = 1;
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
function addRandomGameToRun() {
  if (!isRandomAddValid.value) return;
  const key = `rand-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const seed = (randomFilter.seed && randomFilter.seed.trim().length > 0)
    ? randomFilter.seed.trim()
    : Math.random().toString(36).slice(2, 10);
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
}

function stageRun(mode: 'save' | 'upload') {
  console.log('Stage run', mode, runEntries);
  // Placeholder: integrate with backend/IPC later
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

// Version management
const selectedVersion = ref<number>(1);
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
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
.layout { display: flex; flex-direction: column; height: 100%; font-family: system-ui, sans-serif; }
.toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px; border-bottom: 1px solid #e5e7eb; background: #fafafa; }
.left-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.right-actions { display: flex; align-items: center; gap: 8px; }
.search { min-width: 240px; padding: 6px 8px; }
.status-setter select { margin-left: 6px; }
.toggle { display: inline-flex; align-items: center; gap: 6px; margin-left: 8px; }

.content { flex: 1; display: flex; min-height: 0; }
.table-wrapper { flex: 1; overflow: auto; }
.sidebar { width: 360px; border-left: 1px solid #e5e7eb; padding: 10px; display: flex; flex-direction: column; gap: 10px; overflow: auto; background: #fff; }
.panel { border: 1px solid #e5e7eb; border-radius: 6px; background: #fafafa; }
.panel > h3 { margin: 0; padding: 8px 10px; border-bottom: 1px solid #e5e7eb; font-size: 14px; }
.panel-body { padding: 10px; }
.panel-actions { display: flex; gap: 8px; padding: 8px 10px; border-bottom: 1px solid #e5e7eb; background: #f9fafb; }
.kv-table { width: 100%; border-collapse: collapse; }
.kv-table th { text-align: left; width: 110px; vertical-align: top; padding: 6px; color: #374151; }
.kv-table td { padding: 6px; }
.kv-table input[type="text"], .kv-table input[type="number"], .kv-table textarea, .kv-table select { width: 100%; box-sizing: border-box; padding: 6px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table thead th { position: sticky; top: 0; background: #f3f4f6; z-index: 10; text-align: left; padding: 8px; border-bottom: 1px solid #e5e7eb; }
.data-table tbody td { padding: 8px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
.data-table tbody tr:hover { background: #fafafa; }
.data-table .col-check { width: 36px; text-align: center; }
.data-table .action { width: 40px; text-align: center; font-weight: bold; }
.data-table .name { font-weight: 600; }
.data-table .name.in-run { font-weight: 700; }
.data-table .notes { color: #374151; }
.data-table tbody tr.hidden { opacity: 0.6; }
.data-table tbody tr.finished .name { text-decoration: line-through; color: #6b7280; }
.empty { text-align: center; color: #6b7280; padding: 16px; }

button { padding: 6px 10px; }

/* Modal */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { width: 1200px; max-width: 98vw; max-height: 90vh; background: #fff; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.modal-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 10px; background: #f3f4f6; border-bottom: 1px solid #e5e7eb; }
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

/* Settings Modal */
.settings-modal { width: 800px; max-width: 95vw; }
.settings-body { padding: 20px; max-height: 70vh; overflow-y: auto; }
.settings-section { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb; }
.settings-section:last-child { border-bottom: none; }
.setting-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 8px; }
.setting-label { flex: 0 0 280px; font-weight: 500; display: flex; align-items: center; gap: 8px; }
.status-icon { color: #10b981; font-weight: bold; font-size: 18px; width: 20px; }
.setting-control { flex: 1; display: flex; gap: 8px; align-items: center; }
.setting-control input[type="text"], .setting-control select { flex: 1; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; }
.setting-caption { font-size: 12px; color: #6b7280; margin-top: 4px; margin-left: 300px; line-height: 1.5; }
.setting-caption.warning { color: #d97706; }
.setting-caption code { background: #f3f4f6; padding: 2px 4px; border-radius: 2px; font-size: 11px; }
.setting-caption a { color: #3b82f6; text-decoration: none; }
.setting-caption a:hover { text-decoration: underline; }
.drop-zone { flex: 1; border: 2px dashed #d1d5db; border-radius: 4px; padding: 12px; text-align: center; color: #6b7280; background: #f9fafb; cursor: pointer; transition: all 0.2s; }
.drop-zone:hover { border-color: #3b82f6; background: #eff6ff; color: #3b82f6; }
.modal-footer { padding: 12px 20px; border-top: 1px solid #e5e7eb; display: flex; justify-content: flex-end; background: #f9fafb; }
.btn-primary { padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 4px; font-weight: 500; cursor: pointer; }
.btn-primary:hover { background: #2563eb; }

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
</style>

