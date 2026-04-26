<template>
  <div class="workspace">
    <aside class="sidebar">
      <div class="sidebar-head">
        <h1>MedNet</h1>
        <p>Таблицы БД</p>
      </div>

      <nav class="table-menu">
        <button
          v-for="table in tables"
          :key="table.key"
          class="table-link"
          :class="{ active: selectedTable?.key === table.key }"
          @click="selectTable(table)"
        >
          {{ table.title }}
        </button>
      </nav>
    </aside>

    <div class="content">
      <header class="header">
        <div class="user-block">
          <div class="user-name">{{ currentUser?.username }}</div>
          <div class="user-role">Роль: {{ currentUser?.roleName }}</div>
        </div>
        <div class="header-actions">
          <button v-if="canOpenReports" class="btn btn-secondary" @click="goReports">Отчёты</button>
          <button class="btn btn-danger" @click="logout">Выйти</button>
        </div>
      </header>

      <main class="main">
        <section class="page">
          <h2>{{ selectedTable?.title ?? 'Таблицы' }}</h2>

          <div v-if="error" class="error-box">{{ error }}</div>

          <div class="toolbar">
            <input
              v-model="search"
              class="grow"
              type="text"
              placeholder="Поиск по названию"
              @keyup.enter="loadRows"
            />
            <select
              v-if="selectedTable?.key === 'medicalinstitutions'"
              v-model="institutionType"
              @change="loadRows"
            >
              <option value="">Все типы</option>
              <option value="Hospital">Больница</option>
              <option value="Polyclinic">Поликлиника</option>
              <option value="Laboratory">Лаборатория</option>
            </select>
            <button class="btn btn-secondary" @click="loadRows" :disabled="isLoading">
              {{ isLoading ? 'Загрузка...' : 'Обновить' }}
            </button>
            <button
              v-if="selectedTable?.permissions.canCreate"
              class="btn btn-primary"
              @click="startCreate"
              :disabled="isLoading || columns.length === 0"
            >
              Создать
            </button>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th v-for="column in columns" :key="column.key">{{ column.title }}</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in rows"
                  :key="String(row[selectedTable?.idColumn ?? 'id'])"
                  class="row-clickable"
                  @click="openDetails(row)"
                >
                  <td v-for="column in columns" :key="column.key">
                    {{ formatValue(row[column.key]) }}
                  </td>
                  <td class="actions-cell" @click.stop>
                    <button
                      v-if="selectedTable?.permissions.canUpdate"
                      class="btn btn-secondary"
                      @click="startEdit(row)"
                    >
                      Изменить
                    </button>
                    <button
                      v-if="selectedTable?.permissions.canDelete"
                      class="btn btn-danger"
                      @click="removeRow(row)"
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
                <tr v-if="rows.length === 0">
                  <td :colspan="columns.length + 1" class="muted">Нет данных</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="page details-panel">
          <h2>{{ details?.title ?? 'Детальная информация' }}</h2>
          <p v-if="!details" class="muted">Выберите запись в таблице для просмотра связанных данных.</p>

          <article v-for="section in details?.sections ?? []" :key="section.tableKey" class="card">
            <h3>{{ section.title }}</h3>

            <div v-if="section.rows.length === 0" class="muted">Нет данных</div>
            <div v-else class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th v-for="column in objectColumns(section.rows[0])" :key="column">
                      {{ columnTitle(column) }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in section.rows" :key="index">
                    <td v-for="column in objectColumns(item)" :key="column">
                      {{ formatValue(item[column]) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>
      </main>
    </div>

    <div v-if="createDialog.open" class="modal-backdrop" @click.self="cancelCreate">
      <section class="modal">
        <h3>Создание записи</h3>
        <div class="form-grid">
          <label v-for="(value, key) in createDialog.values" :key="key" class="field">
            <span>{{ columnTitle(key) }}</span>
            <input
              :value="stringValue(value)"
              type="text"
              @input="updateCreateValue(key, ($event.target as HTMLInputElement).value)"
            />
          </label>
        </div>
        <div class="actions">
          <button class="btn btn-primary" @click="saveCreate" :disabled="isSaving">
            {{ isSaving ? 'Сохранение...' : 'Создать' }}
          </button>
          <button class="btn btn-secondary" @click="cancelCreate">Отмена</button>
        </div>
      </section>
    </div>

    <div v-if="editDialog.open" class="modal-backdrop" @click.self="cancelEdit">
      <section class="modal">
        <h3>Редактирование записи #{{ editDialog.rowId }}</h3>
        <div class="form-grid">
          <label v-for="(value, key) in editDialog.values" :key="key" class="field">
            <span>{{ columnTitle(key) }}</span>
            <input
              :value="stringValue(value)"
              type="text"
              @input="updateEditValue(key, ($event.target as HTMLInputElement).value)"
            />
          </label>
        </div>
        <div class="actions">
          <button class="btn btn-primary" @click="saveEdit" :disabled="isSaving">
            {{ isSaving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <button class="btn btn-secondary" @click="cancelEdit">Отмена</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, catalogApi } from '../shared/api'
import { clearAuthState, getStoredUser, setStoredUser } from '../shared/auth'
import { getErrorMessage } from '../shared/http'
import type { AuthMe, ColumnMeta, EntityDetails, TableMeta } from '../shared/types'

type EditDialog = {
  open: boolean
  rowId: number
  values: Record<string, unknown>
}

type CreateDialog = {
  open: boolean
  values: Record<string, unknown>
}

const router = useRouter()
const currentUser = ref<AuthMe | null>(getStoredUser())
const tables = ref<TableMeta[]>([])
const selectedTable = ref<TableMeta | null>(null)
const columns = ref<ColumnMeta[]>([])
const rows = ref<Array<Record<string, unknown>>>([])
const search = ref('')
const institutionType = ref('')
const details = ref<EntityDetails | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)
const error = ref('')
const editDialog = ref<EditDialog>({
  open: false,
  rowId: 0,
  values: {},
})
const createDialog = ref<CreateDialog>({
  open: false,
  values: {},
})

const columnTitleMap = computed(() => {
  const map: Record<string, string> = {}
  for (const column of columns.value) {
    map[column.key] = column.title
  }
  return map
})

const canOpenReports = computed(() => {
  const role = currentUser.value?.roleKey
  return role === 'ADMIN_SYSTEM' || role === 'LABORATORY_SPECIALIST'
})

function columnTitle(columnKey: string): string {
  return columnTitleMap.value[columnKey] ?? columnKey
}

function objectColumns(item: Record<string, unknown>): string[] {
  return Object.keys(item)
}

function stringValue(value: unknown): string {
  if (value === null || value === undefined) {
    return ''
  }
  return String(value)
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'string') {
    const dictionary: Record<string, string> = {
      Hospital: 'Больница',
      Polyclinic: 'Поликлиника',
      Laboratory: 'Лаборатория',
      occupied: 'занято',
      free: 'свободно',
      repair: 'ремонт',
      success: 'успешно',
      fatal: 'летальный исход',
      complications: 'осложнения',
      canceled: 'отменено',
      main: 'основное',
      'part-time': 'совмещение',
      consultation: 'консультация',
    }
    return dictionary[value] ?? value
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

async function loadSessionUser() {
  if (currentUser.value) {
    return
  }
  currentUser.value = await authApi.me()
  setStoredUser(currentUser.value)
}

async function loadTables() {
  tables.value = await catalogApi.listTables()
  if (!tables.value.length) {
    selectedTable.value = null
    columns.value = []
    rows.value = []
    return
  }
  if (!selectedTable.value) {
    selectedTable.value = tables.value[0]
  } else {
    selectedTable.value =
      tables.value.find(item => item.key === selectedTable.value?.key) ?? tables.value[0]
  }
}

async function loadRows() {
  if (!selectedTable.value) {
    return
  }
  try {
    isLoading.value = true
    error.value = ''
    const response = await catalogApi.getRows(selectedTable.value.key, {
      search: search.value.trim() || undefined,
      type:
        selectedTable.value.key === 'medicalinstitutions' && institutionType.value
          ? institutionType.value
          : undefined,
    })
    columns.value = response.columns
    rows.value = response.rows
  } catch (err) {
    error.value = getErrorMessage(err)
  } finally {
    isLoading.value = false
  }
}

async function selectTable(table: TableMeta) {
  selectedTable.value = table
  details.value = null
  search.value = ''
  institutionType.value = ''
  await loadRows()
}

function selectedRowId(row: Record<string, unknown>): number {
  if (!selectedTable.value) {
    return 0
  }
  const rawId = row[selectedTable.value.idColumn]
  return Number(rawId ?? 0)
}

async function openDetails(row: Record<string, unknown>) {
  if (!selectedTable.value) {
    return
  }
  const rowId = selectedRowId(row)
  if (!Number.isFinite(rowId) || rowId <= 0) {
    return
  }
  try {
    error.value = ''
    if (selectedTable.value.key === 'medicalinstitutions') {
      details.value = await catalogApi.getInstitutionDetails(rowId)
      return
    }
    if (selectedTable.value.key === 'employees') {
      details.value = await catalogApi.getEmployeeDetails(rowId)
      return
    }
    if (selectedTable.value.key === 'patients') {
      details.value = await catalogApi.getPatientDetails(rowId)
      return
    }
    details.value = {
      title: `Детали записи #${rowId}`,
      sections: [{ tableKey: selectedTable.value.key, title: selectedTable.value.title, rows: [row] }],
    }
  } catch (err) {
    error.value = getErrorMessage(err)
  }
}

function startEdit(row: Record<string, unknown>) {
  if (!selectedTable.value) {
    return
  }
  const rowId = selectedRowId(row)
  const values: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(row)) {
    if (key === selectedTable.value.idColumn) {
      continue
    }
    values[key] = value
  }
  editDialog.value = {
    open: true,
    rowId,
    values,
  }
}

function startCreate() {
  if (!selectedTable.value || !columns.value.length) {
    return
  }
  const values: Record<string, unknown> = {}
  for (const column of columns.value) {
    values[column.key] = ''
  }
  createDialog.value = {
    open: true,
    values,
  }
}

function updateCreateValue(key: string, value: string) {
  createDialog.value.values[key] = value
}

function cancelCreate() {
  createDialog.value = {
    open: false,
    values: {},
  }
}

function updateEditValue(key: string, value: string) {
  editDialog.value.values[key] = value
}

function cancelEdit() {
  editDialog.value = {
    open: false,
    rowId: 0,
    values: {},
  }
}

async function saveEdit() {
  if (!selectedTable.value || !editDialog.value.open) {
    return
  }
  try {
    isSaving.value = true
    error.value = ''
    await catalogApi.updateRow(selectedTable.value.key, editDialog.value.rowId, editDialog.value.values)
    cancelEdit()
    await loadRows()
  } catch (err) {
    error.value = getErrorMessage(err)
  } finally {
    isSaving.value = false
  }
}

async function saveCreate() {
  if (!selectedTable.value || !createDialog.value.open) {
    return
  }
  try {
    isSaving.value = true
    error.value = ''
    await catalogApi.createRow(selectedTable.value.key, createDialog.value.values)
    cancelCreate()
    await loadRows()
  } catch (err) {
    error.value = getErrorMessage(err)
  } finally {
    isSaving.value = false
  }
}

async function removeRow(row: Record<string, unknown>) {
  if (!selectedTable.value) {
    return
  }
  const rowId = selectedRowId(row)
  if (!window.confirm(`Удалить запись #${rowId}?`)) {
    return
  }
  try {
    error.value = ''
    await catalogApi.deleteRow(selectedTable.value.key, rowId)
    details.value = null
    await loadRows()
  } catch (err) {
    error.value = getErrorMessage(err)
  }
}

async function logout() {
  clearAuthState()
  await router.push({ name: 'login' })
}

async function goReports() {
  await router.push({ name: 'reports' })
}

onMounted(async () => {
  try {
    await loadSessionUser()
    await loadTables()
    await loadRows()
  } catch (err) {
    clearAuthState()
    error.value = getErrorMessage(err)
    await router.push({ name: 'login' })
  }
})
</script>

<style scoped>
.workspace {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px 1fr;
  background: #f5fff6;
  color: #111111;
}

.sidebar {
  border-right: 1px solid #d4ecd7;
  background: #ffffff;
  padding: 16px 12px;
}

.sidebar-head {
  border-bottom: 1px solid #d4ecd7;
  margin-bottom: 10px;
  padding: 8px;
}

.sidebar-head h1 {
  margin: 0;
  font-size: 24px;
}

.sidebar-head p {
  margin: 4px 0 0;
  color: #315a37;
}

.table-menu {
  display: grid;
  gap: 6px;
}

.table-link {
  text-align: left;
  border: 1px solid #d4ecd7;
  border-radius: 8px;
  background: #ffffff;
  color: #111111;
  padding: 8px 10px;
  cursor: pointer;
}

.table-link.active {
  background: #dbf4df;
  border-color: #8fc69a;
}

.content {
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #d4ecd7;
  background: #ffffff;
  padding: 12px 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.user-name {
  font-weight: 700;
}

.user-role {
  color: #315a37;
}

.main {
  padding: 16px;
  display: grid;
  gap: 16px;
}

.details-panel {
  max-height: 48vh;
  overflow: auto;
}

.row-clickable {
  cursor: pointer;
}

.actions-cell {
  width: 230px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  display: grid;
  place-items: center;
  z-index: 20;
}

.modal {
  width: min(860px, 96vw);
  max-height: 80vh;
  overflow: auto;
  background: #ffffff;
  border: 1px solid #d4ecd7;
  border-radius: 12px;
  padding: 16px;
}

@media (min-width: 1200px) {
  .main {
    grid-template-columns: 1.3fr 1fr;
    align-items: start;
  }
}

@media (max-width: 980px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}
</style>
