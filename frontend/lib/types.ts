import type { StatusType } from '~/lib/consts'
import type { Component } from 'vue'

export type KBTableRow = {
  uuid: string
  sourceType: string
  path: string
  content?: string
  status: StatusType
}

export type SelectOption = { label: string; value: string; icon?: string | Component }

export type NullableSelectOption = SelectOption | null
