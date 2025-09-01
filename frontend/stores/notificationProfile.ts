import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { applyBackendErrors } from '~/lib/utils'

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
}

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  type: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  config: z
    .object({
      email: z
        .string()
        .email({ message: 'Invalid email' })
        .optional()
        .or(z.literal('')),
      webhookUrl: z
        .string()
        .url({ message: 'Invalid URL' })
        .optional()
        .or(z.literal('')),
    })
    .refine((data) => data.email || data.webhookUrl, {
      message: 'Either email or webhook URL is required',
    }),
})

type FormValues = z.infer<typeof schema>
const typedSchema = toTypedSchema(schema)

export const useNotificationProfileStore = defineStore('notificationProfiles', {
  state: () => ({
    form: shallowRef<ReturnType<typeof useForm<FormValues>> | null>(null),
    profiles: [] as NotificationProfile[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    initForm() {
      if (!this.form) {
        this.form = useForm<FormValues>({
          validationSchema: typedSchema,
          initialValues: {
            name: '',
            type: '',
            config: {
              email: '',
              webhookUrl: '',
            },
          },
        })
      }
      return this.form
    },

    getFormInstance() {
      return this.initForm()
    },

    setBackendErrors(errors: Record<string, string[] | string>) {
      const formInstance = this.getFormInstance()
      if (!formInstance) return

      applyBackendErrors(formInstance, errors)
    },

    createProfilesPayload(profiles: NotificationProfile[]) {
      return profiles.map(({ name, type, config }) => ({ name, type, config }))
    },

    async load() {
      const { httpGet } = useHttpClient()
      const res = await httpGet<NotificationProfile>('/notification-profiles/')
      this.profiles = Array.isArray(res) ? [...res] : []
      return this.profiles
    },

    async create() {
      if (!this.form) return

      const { values } = this.form

      const { httpPost } = useHttpClient()
      const cleanConfig: NotificationConfig = {}
      if (values.config.email) cleanConfig.email = values.config.email
      if (values.config.webhookUrl)
        cleanConfig.webhookUrl = values.config.webhookUrl

      const response = await httpPost<NotificationProfile>(
        '/notification-profiles/',
        {
          name: values.name,
          type: values.type as NotificationType,
          config: cleanConfig,
        },
      )

      this.profiles = [...this.profiles, response]
      return response
    },
    async createBulkNotificationProfiles(profiles: NotificationProfile[]) {
      const { httpPost } = useHttpClient()
      const payload = this.createProfilesPayload(profiles)

      const response = await httpPost<NotificationProfile>(
        '/notification-profiles/bulk-upload/',
        payload,
      )
      if (Array.isArray(response)) {
        this.profiles = [...this.profiles, ...response]
      }
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
