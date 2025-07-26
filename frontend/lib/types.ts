import type { StatusType } from '~/lib/consts'

export type KBTableRow = {
  uuid: string
  sourceType: string
  path: string
  content?: string
  status: StatusType
}
