<template>
  <SlideOver
    ref="newModelSlideOver"
    title="Create New Model"
  >
    <template #trigger>
      <C8Button label="Create New Model" />
    </template>
    <form class="space-y-5" @submit.prevent="createNewModel">
      <FormField v-slot="{ componentField }" name="name">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Connection Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input v-bind="componentField" placeholder="Ch8r Dev" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <C8Select
        :options="modelTypes"
        :model-value="selectedModelType"
        label="Model Purpose"
        @update:model-value="(val) => (selectedModelType = val)"
      />

      <FormField v-slot="{ componentField }" name="base_url">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Base URL
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              placeholder="https://api.openai.com/v1"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="api_key">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              API Key
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              type="password"
              placeholder="org-YvnH2WW0YjzHn0gAUzh7JY3q"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="model_name">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Model Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input v-bind="componentField" placeholder="gpt-5" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>
    </form>

    <template #submitBtn>
      <C8Button
        label="Create"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="createNewModel"
      />
    </template>
  </SlideOver>
</template>
<script setup lang="ts">
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { computed, ref } from 'vue'
import C8Select from '~/components/C8Select.vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import { setBackendErrors } from '~/lib/utils'

const newModelSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const modelStore = useModelStore()

const modelTypes = [
  { label: 'Text Generation', value: 'text' },
  { label: 'Embedding', value: 'embedding' },
  { label: 'Re-ranking', value: 'reranking' },
]
const selectedModelType = ref(modelTypes[0])

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

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    name: '',
    model_type: '',
    base_url: '',
    api_key: '',
    model_name: '',
  },
})
const { isSubmitting, meta, defineField } = form

const [model_type] = defineField('model_type')

watch(selectedModelType, (val) => {
  model_type.value = val.value
}, { immediate: true })


const createNewModel = form.handleSubmit(async (values) => {
  try {
    await modelStore.create(values)
    newModelSlideOver.value?.closeSlide()
    toast.success('Model created')
  } catch (e: unknown) {
    setBackendErrors(form, e.errors)
  }
})

const disabled = computed(() => !meta.value.valid)
</script>
