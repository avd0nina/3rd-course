import { http } from './http'
import type { AuthMe, EntityDetails, ReportRows, TableMeta, TableRows } from './types'

export const authApi = {
  async me(): Promise<AuthMe> {
    const { data } = await http.get<AuthMe>('/auth/me')
    return data
  },
}

export const catalogApi = {
  async listTables(): Promise<TableMeta[]> {
    const { data } = await http.get<TableMeta[]>('/catalog/tables')
    return data
  },

  async getRows(tableKey: string, params?: { search?: string; type?: string }): Promise<TableRows> {
    const { data } = await http.get<TableRows>(`/catalog/tables/${tableKey}/rows`, { params })
    return data
  },

  async createRow(tableKey: string, payload: Record<string, unknown>): Promise<void> {
    await http.post(`/catalog/tables/${tableKey}/rows`, payload)
  },

  async updateRow(tableKey: string, rowId: number, payload: Record<string, unknown>): Promise<void> {
    await http.put(`/catalog/tables/${tableKey}/rows/${rowId}`, payload)
  },

  async deleteRow(tableKey: string, rowId: number): Promise<void> {
    await http.delete(`/catalog/tables/${tableKey}/rows/${rowId}`)
  },

  async getInstitutionDetails(institutionId: number): Promise<EntityDetails> {
    const { data } = await http.get<EntityDetails>(`/catalog/details/medical-institutions/${institutionId}`)
    return data
  },

  async getEmployeeDetails(employeeId: number): Promise<EntityDetails> {
    const { data } = await http.get<EntityDetails>(`/catalog/details/employees/${employeeId}`)
    return data
  },

  async getPatientDetails(patientId: number): Promise<EntityDetails> {
    const { data } = await http.get<EntityDetails>(`/catalog/details/patients/${patientId}`)
    return data
  },
}

type ReportParams = Record<string, string | number | undefined>

async function fetchReport(path: string, params: ReportParams): Promise<ReportRows> {
  const { data } = await http.get<ReportRows>(path, { params })
  return data
}

export const reportsApi = {
  doctorsBySpecialty(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/doctors/specialty', params)
  },

  supportStaffBySpecialty(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/staff/specialty', params)
  },

  doctorsByOperations(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/doctors/operations', params)
  },

  doctorsByExperience(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/doctors/experience', params)
  },

  doctorsByAcademicData(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/doctors/academic', params)
  },

  currentHospitalPatients(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/patients/current', params)
  },

  hospitalizedPatients(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/patients/hospitalizations', params)
  },

  polyclinicPatientsBySpecialty(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/patients/polyclinic', params)
  },

  hospitalWardStats(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/hospitals/wards', params)
  },

  polyclinicOfficeVisits(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/polyclinics/offices', params)
  },

  doctorProductivity(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/doctors/productivity', params)
  },

  doctorLoad(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/doctors/load', params)
  },

  patientOperations(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/patients/operations', params)
  },

  laboratoryProductivity(params: ReportParams): Promise<ReportRows> {
    return fetchReport('/reports/laboratory/productivity', params)
  },
}
