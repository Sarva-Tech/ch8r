import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'

type NotificationType = 'email' | 'slack' | 'discord'

type NotificationConfig = {
  email?: string
  webhookUrl?: string
}

export type NotificationProfile = {
  id?: number
  uuid?: string
  name: string
  type: NotificationType
  config: NotificationConfig
  created_at?: string
}

type BulkNotificationProfile = Omit<
  NotificationProfile,
  'id' | 'uuid' | 'created_at'
>

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
        return await httpPost<ApiResponse>(
          '/notification-profiles/bulk-upload/',
          payload,
        )
      } catch (err) {
        this.error = 'Failed to create notification profiles'
        console.error(err)
        throw err
      } finally {
        this.loading = false
      }
    },
    async fetchNotificationProfiles() {
      const { httpGet } = useHttpClient()
      this.loading = true
      this.error = null

      try {
        const res = await httpGet<ApiResponse>('/notification-profiles/')
        this.profiles = Array.isArray(res) ? [...res] : []
      } catch (err: any) {
        this.error = err?.message || 'Failed to fetch notification profiles'
        this.profiles = []
        throw err
      } finally {
        this.loading = false
      }
    },
    async delete(id: number | string) {
      this.loading = true

      try {
        const { httpDelete } = useHttpClient()
        await httpDelete(`/notification-profiles/${id}/`)
        this.profiles = this.profiles.filter((profile) => profile.id !== id)
      } catch (err: unknown) {
        console.error('Delete error:', err)
      } finally {
        this.loading = false
      }
    },
    async updateNotificationProfile(updatedProfile: Partial<NotificationProfile>) {
      const { httpPatch } = useHttpClient()
      this.loading = true
      this.error = null

      try {
        const payload: Partial<NotificationProfile> = {}

        if (updatedProfile.name !== undefined) {
          payload.name = updatedProfile.name
        }
        if (updatedProfile.type !== undefined) {
          payload.type = updatedProfile.type
        }
        if (updatedProfile.config !== undefined) {
          payload.config = updatedProfile.config
        }
        const response = await httpPatch<NotificationProfile>(
          `/notification-profiles/${updatedProfile.id}/`,
          payload
        )
        const index = this.profiles.findIndex(p => p.id === updatedProfile.id)
        if (index !== -1) {
          this.profiles[index] = { ...this.profiles[index], ...response }
        }

        return response
      } catch (err) {
        this.error = 'Failed to update notification profile'
        console.error(err)
        throw err
      } finally {
        this.loading = false
      }
    }
  },
})
