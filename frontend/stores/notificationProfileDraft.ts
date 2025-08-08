import { defineStore } from 'pinia'
import { v4 as uuidv4 } from 'uuid'

export type NotificationType = 'discord' | 'slack' | 'email'

export interface NotificationDraftItem {
  id: string
  type: NotificationType
  value: string
  profileName: string
}

interface NotificationStoreState {
  items: NotificationDraftItem[]
}

export const useNotificationDraftStore = defineStore('notificationDraft', {
  state: (): NotificationStoreState => ({
    items: []
  }),

  getters: {
    hasDrafts(): boolean {
      return this.items.length > 0
    },
    discordItems(): NotificationDraftItem[] {
      return this.items.filter(item => item.type === 'discord')
    },
    slackItems(): NotificationDraftItem[] {
      return this.items.filter(item => item.type === 'slack')
    },
    emailItems(): NotificationDraftItem[] {
      return this.items.filter(item => item.type === 'email')
    },
  },

  actions: {
    addItem(type: NotificationType, profileName: string, value: string) {
      if (!profileName.trim() || !value.trim()) {
        throw new Error('Profile name and value are required')
      }

      this.items.push({
        id: uuidv4(),
        type,
        profileName: profileName.trim(),
        value: value.trim()
      })
    },

    setItems(type: NotificationType, values: string[], profileName: string) {
      if (!profileName.trim()) {
        throw new Error('Profile name is required')
      }

      // Remove existing items of the same type
      this.items = this.items.filter(item => item.type !== type)

      // Add new items
      const newItems = values
        .filter(value => value.trim())
        .map(value => ({
          id: uuidv4(),
          type,
          profileName: profileName.trim(),
          value: value.trim()
        }))

      this.items.push(...newItems)
    },

    removeItem(id: string) {
      this.items = this.items.filter(item => item.id !== id)
    },

    clear() {
      this.items = []
    }
  }
})