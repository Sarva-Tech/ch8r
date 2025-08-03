import type { StatusType } from '~/lib/consts'

export type KBTableRow = {
  uuid: string
  sourceType: string
  path: string
  content?: string
  status: StatusType
}

export type APIKeyTableRow = {
  name: string
  read: boolean
  write: boolean
  delete: boolean
  created: string
}
