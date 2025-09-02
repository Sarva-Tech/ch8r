import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { applyBackendErrors } from '~/lib/utils'

export type LLMModelType = 'text' | 'embedding' | 'image' | 'rerank' | 'other'

export interface LLMModel {
  id: number
  uuid: string

  owner: number

  name: string
  api_key?: string | null
  base_url?: string | null
  model_name: string

  model_type: LLMModelType
  is_default: boolean

  created_at: string
}

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  model_type: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  base_url: z
    .string()
    .nonempty({ message: 'Required' })
    .min(1)
    .max(255)
    .url({ message: 'Invalid URL' }),
  api_key: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  model_name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
})

type FormValues = z.infer<typeof schema>
const typedSchema = toTypedSchema(schema)

export const useModelStore = defineStore('model', {
  state: () => ({
    form: shallowRef<ReturnType<typeof useForm<FormValues>> | null>(null),
    models: [] as LLMModel[],
  }),

  actions: {
    initForm() {
      if (!this.form) {
        this.form = useForm<FormValues>({
          validationSchema: typedSchema,
          initialValues: {
            name: '',
            model_type: '',
            base_url: '',
            api_key: '',
            model_name: '',
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

    async load() {
      const { httpGet } = useHttpClient()
      const response = await httpGet<LLMModel[]>(`/models/`)
      this.models = response
      return response
    },

    async create() {
      if (!this.form) return

      const { handleSubmit } = this.form

      return handleSubmit(async (values: FormValues) => {
        const { httpPost } = useHttpClient()
        const response = await httpPost<LLMModel>('/models/', {
          name: values.name,
          api_key: values.api_key,
          base_url: values.base_url,
          model_name: values.model_name,
          model_type: values.model_type,
        })
        this.models = [...this.models, response]
        return response
      })()
    },
  },
})
