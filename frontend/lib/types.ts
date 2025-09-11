import type { StatusType } from '~/lib/consts'

export type KBTableRow = {
  uuid: string
  sourceType: string
  path: string
  content?: string
  status: StatusType
}

export interface SelectOption {
  label: string
  value: string
  selected: boolean
}

