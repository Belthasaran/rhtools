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
              <th>Id</th>
              <th>Name</th>
              <th>Type</th>
              <th>Author</th>
              <th>Length</th>
              <th>Status</th>
              <th>My rating</th>
              <th>Public rating</th>
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
                <input type="checkbox" v-model="selectedIdsSetProxy[row.Id]" @click.stop />
              </td>
              <td>{{ row.Id }}</td>
              <td class="name">{{ row.Name }}</td>
              <td>{{ row.Type }}</td>
              <td>{{ row.Author }}</td>
              <td>{{ row.Length }}</td>
              <td>{{ row.Status }}</td>
              <td>{{ row.Myrating ?? '' }}</td>
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
                <tr><th>Id</th><td>{{ selectedItem.Id }}</td></tr>
                <tr><th>Name</th><td><input v-model="selectedItem.Name" /></td></tr>
                <tr><th>Type</th><td><input v-model="selectedItem.Type" /></td></tr>
                <tr><th>Author</th><td><input v-model="selectedItem.Author" /></td></tr>
                <tr><th>Length</th><td><input v-model="selectedItem.Length" /></td></tr>
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
                <tr><th>My rating</th><td><input type="number" min="0" max="5" step="0.5" v-model.number="selectedItem.Myrating" /></td></tr>
                <tr><th>Public rating</th><td><input type="number" min="0" max="5" step="0.1" v-model.number="selectedItem.Publicrating" /></td></tr>
                <tr>
                  <th>Hidden</th>
                  <td><input type="checkbox" v-model="selectedItem.Hidden" /></td>
                </tr>
                <tr>
                  <th>My notes</th>
                  <td><textarea v-model="selectedItem.Mynotes" rows="4"></textarea></td>
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
            <button @click="setStageRating" :disabled="selectedStageIds.size === 0">My rating</button>
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
                  <th>Rating</th>
                  <th>My notes</th>
                  <th>My rating</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="st in currentStages" :key="st.key">
                  <td class="col-check"><input type="checkbox" :checked="selectedStageIds.has(st.key)" @change="toggleStageSelection(st.key, $event)" /></td>
                  <td>{{ st.parentId }}</td>
                  <td>{{ st.exitNumber }}</td>
                  <td>{{ st.description }}</td>
                  <td>{{ st.publicRating ?? '' }}</td>
                  <td>{{ st.myNotes ?? '' }}</td>
                  <td>{{ st.myRating ?? '' }}</td>
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
  
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

type ItemStatus = 'Default' | 'In Progress' | 'Finished';

type Item = {
  Id: string;
  Name: string;
  Type: string;
  Author: string;
  Length: string;
  Status: ItemStatus;
  Myrating?: number;
  Publicrating?: number;
  Hidden: boolean;
  Mynotes?: string;
};

const items = reactive<Item[]>([
  { Id: '11374', Name: 'Super Dram World', Type: 'Kaizo: Intermediate', Author: 'Panga', Length: '18 exits', Status: 'Default', Myrating: 4, Publicrating: 4.3, Hidden: false, Mynotes: '' },
  { Id: '17289', Name: 'Storks, Apes, and Crocodiles', Type: 'Standard', Author: 'Morsel', Length: 'unknown', Status: 'In Progress', Myrating: 5, Publicrating: 4.6, Hidden: false, Mynotes: 'Practice level 0x0F' },
  { Id: '20091', Name: 'Example Hack', Type: 'Traditional', Author: 'Someone', Length: '5 exits', Status: 'Finished', Myrating: 3, Publicrating: 3.8, Hidden: false, Mynotes: '' },
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
      String(it.Myrating ?? ''),
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

const selectedIdsSetProxy = computed<Record<string, boolean>>({
  get() {
    const record: Record<string, boolean> = {};
    for (const it of filteredItems.value) record[it.Id] = selectedIds.value.has(it.Id);
    return record;
  },
  set(next) {
    const newSet = new Set<string>();
    for (const [id, checked] of Object.entries(next)) {
      if (checked) newSet.add(id);
    }
    selectedIds.value = newSet;
  },
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

function openSettings() {
  console.log('Open settings');
}

// Right-side panels state and helpers
type Stage = {
  key: string; // unique key: `${parentId}-${exitNumber}`
  parentId: string;
  exitNumber: string;
  description: string;
  publicRating?: number;
  myNotes?: string;
  myRating?: number;
};

// Demo stage data per item id
const stagesByItemId = reactive<Record<string, Stage[]>>({
  '11374': [
    { key: '11374-1', parentId: '11374', exitNumber: '1', description: 'Intro stage', publicRating: 4.2, myNotes: '', myRating: 4 },
    { key: '11374-2', parentId: '11374', exitNumber: '2', description: 'Shell level', publicRating: 4.5, myNotes: 'practice', myRating: 5 },
  ],
  '17289': [
    { key: '17289-0x0F', parentId: '17289', exitNumber: '0x0F', description: 'Custom level jump', publicRating: 4.6, myNotes: 'good practice', myRating: 5 },
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
  console.log('Add stages to run:', ids);
}

function editStageNotes() {
  const ids = Array.from(selectedStageIds.value.values());
  if (ids.length === 0) return;
  const next = window.prompt('Set notes for selected stages:');
  if (next === null) return;
  for (const st of currentStages.value) if (selectedStageIds.value.has(st.key)) st.myNotes = next;
}

function setStageRating() {
  const ids = Array.from(selectedStageIds.value.values());
  if (ids.length === 0) return;
  const next = window.prompt('Set My rating (0-5) for selected stages:');
  if (next === null) return;
  const n = Number(next);
  if (Number.isNaN(n) || n < 0 || n > 5) return;
  for (const st of currentStages.value) if (selectedStageIds.value.has(st.key)) st.myRating = n;
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
.data-table thead th { position: sticky; top: 0; background: #f3f4f6; z-index: 1; text-align: left; padding: 8px; border-bottom: 1px solid #e5e7eb; }
.data-table tbody td { padding: 8px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
.data-table tbody tr:hover { background: #fafafa; }
.data-table .col-check { width: 36px; text-align: center; }
.data-table .name { font-weight: 600; }
.data-table .notes { color: #374151; }
.data-table tbody tr.hidden { opacity: 0.6; }
.data-table tbody tr.finished .name { text-decoration: line-through; color: #6b7280; }
.empty { text-align: center; color: #6b7280; padding: 16px; }

button { padding: 6px 10px; }
</style>

