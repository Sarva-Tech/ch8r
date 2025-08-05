import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'

type NotificationType = 'email' | 'slack' | 'discord'

type NotificationConfig = {
  email?: string
  webhookUrl?: string
}

type NotificationProfile = {
  id?: number
  uuid?: string
  name: string
  type: NotificationType
  config: NotificationConfig
  created_at?: string
}

type BulkNotificationProfile = Omit<NotificationProfile, 'id' | 'uuid' | 'created_at'>

type ApiResponse = {
  status: string
  message: string
  count: number
  data?: NotificationProfile[]
}

export const useNotificationProfileStore = defineStore('notificationProfiles', {
  state: () => ({
    profiles: [] as NotificationProfile[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    createProfilesPayload(profiles: BulkNotificationProfile[]) {
      return profiles.map(({ name, type, config }) => ({ name, type, config }))
    },

    async createBulkNotificationProfiles(profiles: BulkNotificationProfile[]) {
      const { httpPost } = useHttpClient()
      this.loading = true
      this.error = null

      try {
        const payload = this.createProfilesPayload(profiles)
        const res = await httpPost<ApiResponse>('/notification-profiles/bulk-upload/', payload)
        return res
      } catch (err) {
        this.error = 'Failed to create notification profiles'
        console.error(err)
        throw err
      } finally {
        this.loading = false
      }
    },
  },
})
