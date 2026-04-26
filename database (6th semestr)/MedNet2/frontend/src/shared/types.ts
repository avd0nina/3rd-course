export type RoleKey = 'ADMIN_SYSTEM' | 'LABORATORY_SPECIALIST'

export interface AuthMe {
  username: string
  roleKey: RoleKey
  roleName: string
}

export interface TablePermission {
  canRead: boolean
  canCreate: boolean
  canUpdate: boolean
  canDelete: boolean
}

export interface TableMeta {
  key: string
  tableName: string
  title: string
  idColumn: string
  permissions: TablePermission
}

export interface ColumnMeta {
  key: string
  title: string
}

export interface TableRows {
  columns: ColumnMeta[]
  rows: Array<Record<string, unknown>>
  permissions: TablePermission
}

export interface DetailSection {
  tableKey: string
  title: string
  rows: Array<Record<string, unknown>>
}

export interface EntityDetails {
  title: string
  sections: DetailSection[]
}

export type ReportRows = Array<Record<string, unknown>>
