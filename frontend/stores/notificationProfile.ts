import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type { PaginatedResponse } from '~/lib/types'
import { getErrorMessage } from '~/lib/utils'

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
  owner: number
  config: NotificationConfig
  created_at?: string
  is_enabled?: boolean
}

export type NotificationProfileResponse = PaginatedResponse<NotificationProfile>

export const useNotificationProfileStore = defineStore('notificationProfiles', {
  state: () => ({
    profiles: [] as NotificationProfile[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    getBackendErrorMessage(error: any): string {
      if (error.errors?.config) {
        if (typeof error.errors.config === 'object' && error.errors.config.webhookUrl) {
          return error.errors.config.webhookUrl
        } else if (typeof error.errors.config === 'string') {
          return error.errors.config
        } else if (Array.isArray(error.errors.config)) {
          return error.errors.config.join(', ')
        }
      }
      
      if (error.errors?.type) return error.errors.type
      if (error.errors?.name) return error.errors.name
      if (typeof error.errors === 'string') return error.errors
      
      return getErrorMessage(error) || 'Operation failed'
    },

    async load() {
      const { httpGet } = useHttpClient()
      const res = await httpGet<NotificationProfileResponse>('/notification-profiles/')
      this.profiles = res.results || []
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
    async delete(uuid: string) {
      const { httpDelete } = useHttpClient()
      try {
        const response = await httpDelete<{detail: string}>(`/notification-profiles/${uuid}/`)
        this.profiles = this.profiles.filter((profile) => profile.uuid !== uuid)
        return response
      } catch (error) {
        throw error
      }
    },

    async update(
      uuid: string,
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
        `/notification-profiles/${uuid}/`,
        payload,
      )
      const index = this.profiles.findIndex((profile) => profile.uuid === uuid)
      if (index !== -1) {
        this.profiles[index] = { ...this.profiles[index], ...response }
      }
      return response
    },
  },
})
