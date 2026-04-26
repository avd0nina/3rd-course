<template>
  <div class="workspace">
    <aside class="sidebar">
      <div class="sidebar-head">
        <h1>MedNet</h1>
        <p>SQL-отчёты</p>
      </div>

      <nav class="report-menu">
        <button
          v-for="report in availableReports"
          :key="report.key"
          class="report-link"
          :class="{ active: selectedReport.key === report.key }"
          @click="selectReport(report.key)"
        >
          {{ report.shortTitle }}
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
          <button class="btn btn-secondary" @click="goTables">Таблицы</button>
          <button class="btn btn-danger" @click="logout">Выйти</button>
        </div>
      </header>

      <main class="main">
        <section class="page">
          <h2>{{ selectedReport.title }}</h2>
          <p class="muted">{{ selectedReport.description }}</p>

          <div v-if="error" class="error-box">{{ error }}</div>

          <div class="form-grid">
            <label v-for="field in selectedReport.fields" :key="field.key" class="field">
              <span>
                {{ field.label }}
                <strong v-if="field.required"> *</strong>
              </span>
              <select
                v-if="field.type === 'select'"
                :value="fieldValue(field.key)"
                @change="setFieldValue(field.key, ($event.target as HTMLSelectElement).value)"
              >
                <option value="">Не выбрано</option>
                <option v-for="option in field.options ?? []" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <input
                v-else
                :value="fieldValue(field.key)"
                :type="field.type"
                :placeholder="field.placeholder ?? ''"
                @input="setFieldValue(field.key, ($event.target as HTMLInputElement).value)"
              />
            </label>
          </div>

          <div class="actions">
            <button class="btn btn-primary" :disabled="isLoading" @click="runReport">
              {{ isLoading ? 'Выполняется...' : 'Выполнить запрос' }}
            </button>
            <button class="btn btn-secondary" :disabled="isLoading" @click="resetFilters">
              Сбросить фильтры
            </button>
          </div>
        </section>

        <section class="page">
          <h3>Результат</h3>

          <div class="summary">
            <span class="summary-item">Строк: {{ rows.length }}</span>
            <span v-for="metric in summaryMetrics" :key="metric.key" class="summary-item">
              {{ metric.label }}: {{ metric.value }}
            </span>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th v-for="column in columns" :key="column">{{ columnTitle(column) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in rows" :key="index">
                  <td v-for="column in columns" :key="column">{{ formatValue(row[column]) }}</td>
                </tr>
                <tr v-if="rows.length === 0">
                  <td :colspan="Math.max(columns.length, 1)" class="muted">Нет данных</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, reportsApi } from '../shared/api'
import { clearAuthState, getStoredUser, setStoredUser } from '../shared/auth'
import { getErrorMessage } from '../shared/http'
import type { AuthMe, ReportRows } from '../shared/types'

type FieldType = 'text' | 'number' | 'date' | 'select'
type ReportParams = Record<string, string | number | undefined>

type SelectOption = {
  value: string
  label: string
}

type ReportField = {
  key: string
  label: string
  type: FieldType
  required?: boolean
  placeholder?: string
  options?: SelectOption[]
}

type ReportDefinition = {
  key: string
  shortTitle: string
  title: string
  description: string
  fields: ReportField[]
  anyOf?: string[]
  fetcher: (params: ReportParams) => Promise<ReportRows>
}

type SummaryMetric = {
  key: string
  label: string
  value: string
}

const institutionTypeOptions: SelectOption[] = [
  { value: 'Hospital', label: 'Больница' },
  { value: 'Polyclinic', label: 'Поликлиника' },
  { value: 'Laboratory', label: 'Лаборатория' },
]

const reportDefinitions: ReportDefinition[] = [
  {
    key: 'q1',
    shortTitle: '1. Врачи по профилю',
    title: '1. Врачи указанного профиля',
    description: 'Перечень и общее число врачей по профилю для учреждения / типа учреждения / города.',
    fields: [
      { key: 'specialty', label: 'Профиль врача', type: 'text', required: true, placeholder: 'Например: Хирург' },
      { key: 'institutionId', label: 'ID учреждения', type: 'number' },
      { key: 'institutionType', label: 'Тип учреждения', type: 'select', options: institutionTypeOptions },
      { key: 'city', label: 'Город', type: 'text', placeholder: 'Например: Москва' },
    ],
    fetcher: reportsApi.doctorsBySpecialty,
  },
  {
    key: 'q2',
    shortTitle: '2. Персонал по специальности',
    title: '2. Обслуживающий персонал указанной специальности',
    description: 'Перечень и общее число сотрудников обслуживающего персонала.',
    fields: [
      { key: 'specialty', label: 'Специальность персонала', type: 'text', required: true },
      { key: 'institutionId', label: 'ID учреждения', type: 'number' },
      { key: 'institutionType', label: 'Тип учреждения', type: 'select', options: institutionTypeOptions },
      { key: 'city', label: 'Город', type: 'text' },
    ],
    fetcher: reportsApi.supportStaffBySpecialty,
  },
  {
    key: 'q3',
    shortTitle: '3. Врачи + минимум операций',
    title: '3. Врачи профиля с числом операций не менее заданного',
    description: 'Врачи нужного профиля, у которых количество операций не меньше порога.',
    fields: [
      { key: 'specialty', label: 'Профиль врача', type: 'text', required: true },
      { key: 'minOperations', label: 'Минимум операций', type: 'number', required: true, placeholder: '0' },
      { key: 'institutionId', label: 'ID учреждения', type: 'number' },
      { key: 'institutionType', label: 'Тип учреждения', type: 'select', options: institutionTypeOptions },
      { key: 'city', label: 'Город', type: 'text' },
    ],
    fetcher: reportsApi.doctorsByOperations,
  },
  {
    key: 'q4',
    shortTitle: '4. Врачи + минимум стажа',
    title: '4. Врачи профиля со стажем не менее заданного',
    description: 'Врачи указанного профиля с фильтром по минимальному стажу.',
    fields: [
      { key: 'specialty', label: 'Профиль врача', type: 'text', required: true },
      { key: 'minExperience', label: 'Минимальный стаж (лет)', type: 'number', required: true, placeholder: '0' },
      { key: 'institutionId', label: 'ID учреждения', type: 'number' },
      { key: 'institutionType', label: 'Тип учреждения', type: 'select', options: institutionTypeOptions },
      { key: 'city', label: 'Город', type: 'text' },
    ],
    fetcher: reportsApi.doctorsByExperience,
  },
  {
    key: 'q5',
    shortTitle: '5. Врачи со степенью/званием',
    title: '5. Врачи профиля со степенью и званием',
    description: 'Врачи профиля со степенью кандидата/доктора и званием доцента/профессора.',
    fields: [
      { key: 'specialty', label: 'Профиль врача', type: 'text', required: true },
      { key: 'institutionId', label: 'ID учреждения', type: 'number' },
      { key: 'institutionType', label: 'Тип учреждения', type: 'select', options: institutionTypeOptions },
      { key: 'city', label: 'Город', type: 'text' },
    ],
    fetcher: reportsApi.doctorsByAcademicData,
  },
  {
    key: 'q6',
    shortTitle: '6. Пациенты больницы/отделения/палаты',
    title: '6. Текущие пациенты больницы, отделения или палаты',
    description: 'Список пациентов с датой поступления, состоянием и лечащим врачом.',
    fields: [
      { key: 'hospitalId', label: 'ID больницы', type: 'number', required: true },
      { key: 'departmentId', label: 'ID отделения', type: 'number' },
      { key: 'wardId', label: 'ID палаты', type: 'number' },
      { key: 'wardNumber', label: 'Номер палаты', type: 'number' },
    ],
    fetcher: reportsApi.currentHospitalPatients,
  },
  {
    key: 'q7',
    shortTitle: '7. Стационар за период',
    title: '7. Пациенты, прошедшие стационарное лечение за период',
    description: 'Фильтр по больнице или врачу. Даты обязательны.',
    fields: [
      { key: 'hospitalId', label: 'ID больницы', type: 'number' },
      { key: 'doctorId', label: 'ID врача', type: 'number' },
      { key: 'startDate', label: 'Дата начала', type: 'date', required: true },
      { key: 'endDate', label: 'Дата окончания', type: 'date', required: true },
    ],
    anyOf: ['hospitalId', 'doctorId'],
    fetcher: reportsApi.hospitalizedPatients,
  },
  {
    key: 'q8',
    shortTitle: '8. Пациенты поликлиники по профилю',
    title: '8. Пациенты у врача указанного профиля в поликлинике',
    description: 'Список пациентов, наблюдающихся у врачей заданного профиля.',
    fields: [
      { key: 'specialty', label: 'Профиль врача', type: 'text', required: true },
      { key: 'polyclinicId', label: 'ID поликлиники', type: 'number', required: true },
    ],
    fetcher: reportsApi.polyclinicPatientsBySpecialty,
  },
  {
    key: 'q9',
    shortTitle: '9. Палаты и койки больницы',
    title: '9. Палаты и койки больницы (всего и по отделениям)',
    description: 'Общее число палат/коек, свободные койки и полностью свободные палаты.',
    fields: [{ key: 'hospitalId', label: 'ID больницы', type: 'number', required: true }],
    fetcher: reportsApi.hospitalWardStats,
  },
  {
    key: 'q10',
    shortTitle: '10. Кабинеты и посещения',
    title: '10. Кабинеты поликлиники и посещения за период',
    description: 'Число кабинетов и число посещений каждого кабинета за период.',
    fields: [
      { key: 'polyclinicId', label: 'ID поликлиники', type: 'number', required: true },
      { key: 'startDate', label: 'Дата начала', type: 'date', required: true },
      { key: 'endDate', label: 'Дата окончания', type: 'date', required: true },
    ],
    fetcher: reportsApi.polyclinicOfficeVisits,
  },
  {
    key: 'q11',
    shortTitle: '11. Выработка врачей',
    title: '11. Выработка врачей (среднее число пациентов в день)',
    description: 'Для конкретного врача, всех врачей поликлиники или врачей указанного профиля.',
    fields: [
      { key: 'startDate', label: 'Дата начала', type: 'date', required: true },
      { key: 'endDate', label: 'Дата окончания', type: 'date', required: true },
      { key: 'doctorId', label: 'ID врача', type: 'number' },
      { key: 'polyclinicId', label: 'ID поликлиники', type: 'number' },
      { key: 'specialty', label: 'Профиль врача', type: 'text' },
    ],
    anyOf: ['doctorId', 'polyclinicId', 'specialty'],
    fetcher: reportsApi.doctorProductivity,
  },
  {
    key: 'q12',
    shortTitle: '12. Загрузка врачей',
    title: '12. Загрузка врачей (число текущих пациентов)',
    description: 'Для конкретного врача, всех врачей больницы или врачей профиля.',
    fields: [
      { key: 'doctorId', label: 'ID врача', type: 'number' },
      { key: 'hospitalId', label: 'ID больницы', type: 'number' },
      { key: 'specialty', label: 'Профиль врача', type: 'text' },
    ],
    anyOf: ['doctorId', 'hospitalId', 'specialty'],
    fetcher: reportsApi.doctorLoad,
  },
  {
    key: 'q13',
    shortTitle: '13. Пациенты после операций',
    title: '13. Пациенты, перенесшие операции за период',
    description: 'Фильтры по учреждению, типу учреждения и врачу.',
    fields: [
      { key: 'institutionId', label: 'ID учреждения', type: 'number' },
      { key: 'institutionType', label: 'Тип учреждения', type: 'select', options: institutionTypeOptions },
      { key: 'doctorId', label: 'ID врача', type: 'number' },
      { key: 'startDate', label: 'Дата начала', type: 'date', required: true },
      { key: 'endDate', label: 'Дата окончания', type: 'date', required: true },
    ],
    fetcher: reportsApi.patientOperations,
  },
  {
    key: 'q14',
    shortTitle: '14. Выработка лаборатории',
    title: '14. Выработка лаборатории за период',
    description: 'Среднее число обследований в день для учреждения или всех лабораторий города.',
    fields: [
      { key: 'institutionId', label: 'ID учреждения', type: 'number' },
      { key: 'city', label: 'Город', type: 'text' },
      { key: 'startDate', label: 'Дата начала', type: 'date', required: true },
      { key: 'endDate', label: 'Дата окончания', type: 'date', required: true },
    ],
    fetcher: reportsApi.laboratoryProductivity,
  },
]

function createInitialFilterValues(report: ReportDefinition): Record<string, string> {
  const values: Record<string, string> = {}
  for (const field of report.fields) {
    values[field.key] = ''
  }
  return values
}

const router = useRouter()
const currentUser = ref<AuthMe | null>(getStoredUser())

// Фильтруем отчёты в зависимости от роли
const availableReports = computed(() => {
  if (currentUser.value?.roleKey === 'LABORATORY_SPECIALIST') {
    // Специалист лаборатории видит только отчёт 14 (выработка лаборатории)
    return reportDefinitions.filter(r => r.key === 'q14')
  }
  // Администраторы видят все отчёты
  return reportDefinitions
})

const selectedReportKey = ref(availableReports.value[0]?.key ?? reportDefinitions[0].key)
const rows = ref<ReportRows>([])
const error = ref('')
const isLoading = ref(false)
const filtersByReport = ref<Record<string, Record<string, string>>>(
  Object.fromEntries(reportDefinitions.map(report => [report.key, createInitialFilterValues(report)])),
)

const selectedReport = computed(
  () => availableReports.value.find(report => report.key === selectedReportKey.value) ?? availableReports.value[0],
)

const columns = computed(() => {
  if (!rows.value.length) {
    return []
  }
  return Object.keys(rows.value[0])
})

const summaryMetrics = computed<SummaryMetric[]>(() => {
  if (!rows.value.length) {
    return []
  }
  const firstRow = rows.value[0]
  const metrics: SummaryMetric[] = []
  for (const [key, value] of Object.entries(firstRow)) {
    if (typeof value !== 'number') {
      continue
    }
    const normalized = key.toLowerCase()
    if (
      normalized.includes('total') ||
      normalized.includes('всего') ||
      normalized.includes('общее') ||
      normalized.includes('obshee') ||
      normalized.includes('vsego')
    ) {
      metrics.push({
        key,
        label: columnTitle(key),
        value: String(value),
      })
    }
  }
  return metrics
})

const canUseReports = computed(() => {
  const role = currentUser.value?.roleKey
  return role === 'ADMIN_SYSTEM' || role === 'LABORATORY_SPECIALIST'
})

function fieldValue(fieldKey: string): string {
  return filtersByReport.value[selectedReport.value.key]?.[fieldKey] ?? ''
}

function setFieldValue(fieldKey: string, value: string) {
  const reportFilters = filtersByReport.value[selectedReport.value.key]
  if (!reportFilters) {
    return
  }
  reportFilters[fieldKey] = value
}

function selectReport(reportKey: string) {
  selectedReportKey.value = reportKey
  rows.value = []
  error.value = ''
}

function resetFilters() {
  filtersByReport.value[selectedReport.value.key] = createInitialFilterValues(selectedReport.value)
  rows.value = []
  error.value = ''
}

function hasFilledValue(value: string): boolean {
  return value.trim().length > 0
}

function validate(report: ReportDefinition): string | null {
  const values = filtersByReport.value[report.key]
  for (const field of report.fields) {
    if (field.required && !hasFilledValue(values[field.key] ?? '')) {
      return `Поле "${field.label}" обязательно`
    }
  }

  if (report.anyOf?.length) {
    const hasAny = report.anyOf.some(fieldKey => hasFilledValue(values[fieldKey] ?? ''))
    if (!hasAny) {
      const labels = report.anyOf.map(
        fieldKey => report.fields.find(field => field.key === fieldKey)?.label ?? fieldKey,
      )
      return `Нужно заполнить хотя бы одно из полей: ${labels.join(', ')}`
    }
  }

  const startDate = values.startDate?.trim()
  const endDate = values.endDate?.trim()
  if (startDate && endDate && startDate > endDate) {
    return 'Дата окончания должна быть не раньше даты начала'
  }

  return null
}

function buildParams(report: ReportDefinition): ReportParams {
  const values = filtersByReport.value[report.key]
  const params: ReportParams = {}

  for (const field of report.fields) {
    const rawValue = (values[field.key] ?? '').trim()
    if (!rawValue) {
      continue
    }

    if (field.type === 'number') {
      const numericValue = Number(rawValue)
      if (!Number.isFinite(numericValue)) {
        throw new Error(`Поле "${field.label}" должно быть числом`)
      }
      params[field.key] = numericValue
      continue
    }

    params[field.key] = rawValue
  }

  return params
}

function columnTitle(columnKey: string): string {
  return columnKey.replaceAll('_', ' ')
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
      low: 'низкая',
      medium: 'средняя',
      high: 'высокая',
      none: 'нет',
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

async function runReport() {
  if (!canUseReports.value) {
    error.value = 'Отчёты доступны только администраторам и специалистам лабораторий'
    return
  }

  const validationMessage = validate(selectedReport.value)
  if (validationMessage) {
    error.value = validationMessage
    return
  }

  try {
    isLoading.value = true
    error.value = ''
    const params = buildParams(selectedReport.value)
    rows.value = await selectedReport.value.fetcher(params)
  } catch (err) {
    error.value = getErrorMessage(err)
    rows.value = []
  } finally {
    isLoading.value = false
  }
}

async function goTables() {
  await router.push({ name: 'tables' })
}

async function logout() {
  clearAuthState()
  await router.push({ name: 'login' })
}

onMounted(async () => {
  try {
    await loadSessionUser()
    if (!canUseReports.value) {
      error.value = 'Отчёты доступны только пользователю с ролью "Администратор системы"'
    }
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
  grid-template-columns: 340px 1fr;
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

.report-menu {
  display: grid;
  gap: 6px;
}

.report-link {
  text-align: left;
  border: 1px solid #d4ecd7;
  border-radius: 8px;
  background: #ffffff;
  color: #111111;
  padding: 8px 10px;
  cursor: pointer;
}

.report-link.active {
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

.user-name {
  font-weight: 700;
}

.user-role {
  color: #315a37;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.main {
  padding: 16px;
  display: grid;
  gap: 16px;
}

.summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.summary-item {
  background: #edf9ef;
  border: 1px solid #c9e6cf;
  border-radius: 20px;
  padding: 4px 10px;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}
</style>
