import { defineStore } from 'pinia'

export type DraftSourceType = 'file' | 'text' | 'url'

export interface DraftItem {
  id: string
  type: DraftSourceType
  value: File | string
}

export const useKBDraftStore = defineStore('kbDraft', {
  state: () => ({
    items: [] as DraftItem[]
  }),

  getters: {
    hasDrafts: (state) => state.items.length > 0,
    files: (state) => state.items.filter((item) => item.type === 'file') as DraftItem[],
    texts: (state) => state.items.filter((item) => item.type === 'text') as DraftItem[],
    urls: (state) => state.items.filter((item) => item.type === 'url') as DraftItem[],
  },

  actions: {
    addFile(file: File) {
      this.items.push({ id: crypto.randomUUID(), type: 'file', value: file })
    },
    setFiles(files: File[]) {
      this.items = this.items.filter(item => item.type !== 'file')

      const newFileItems = files.map(file => ({
        id: crypto.randomUUID(),
        type: 'file' as const,
        value: file
      }))

      this.items.push(...newFileItems)
    },
    addText(text: string) {
      this.items.push({ id: crypto.randomUUID(), type: 'text', value: text })
    },
    addUrl(url: string) {
      this.items.push({ id: crypto.randomUUID(), type: 'url', value: url })
    },
    remove(id: string) {
      this.items = this.items.filter((item) => item.id !== id)
    },
    clear() {
      this.items = []
    }
  },
})
