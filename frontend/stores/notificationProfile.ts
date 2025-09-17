import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'

export type NotificationType = 'email' | 'slack' | 'discord'

export type NotificationConfig = {
  email?: string
  webhookUrl?: string
}

export interface NotificationProfile {
  id?: number
  uuid?: string
  name: string
  type: NotificationType
  config: NotificationConfig
  created_at?: string
  is_enabled?: boolean
}

export const useNotificationProfileStore = defineStore('notificationProfiles', {
  state: () => ({
    profiles: [] as NotificationProfile[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    async load() {
      const { httpGet } = useHttpClient()
      const res = await httpGet<NotificationProfile>('/notification-profiles/')
      this.profiles = Array.isArray(res) ? [...res] : []
      return this.profiles
    },

    async create(values: Record<string, unknown>) {
      const { httpPost } = useHttpClient()

      const response = await httpPost<NotificationProfile>(
        '/notification-profiles/',
        {
          name: values.name,
          type: values.type as NotificationType,
          config: {
            email: values.email,
            webhookUrl: values.webhookUrl
          },
        },
      )

      this.profiles = [...this.profiles, response]
      return response
    },
    async delete(id: number | string) {
      const { httpDelete } = useHttpClient()
      await httpDelete(`/notification-profiles/${id}/`)
      this.profiles = this.profiles.filter((profile) => profile.id !== id)
    },

    async update(
      id: number | string,
      updatedProfile: Partial<NotificationProfile>,
    ) {
      const { httpPatch } = useHttpClient()

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
        `/notification-profiles/${id}/`,
        payload,
      )
      const index = this.profiles.findIndex((profile) => profile.id === id)
      if (index !== -1) {
        this.profiles[index] = { ...this.profiles[index], ...response }
      }
      return response
    },
  },
})
