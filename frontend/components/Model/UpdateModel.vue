<template>
  <SlideOver ref="updateModelSlide" title="Update Model">
    <form class="space-y-5" @submit.prevent="updateModel">
      <C8Select
        :options="ModelTypes"
        :model-value="selectedModelType"
        label="Model Purpose"
        disabled
      />

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
          <FormDescription>
            Leave the API key field blank to keep the existing key.
          </FormDescription>
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
        label="Update"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="updateModel"
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
import { ModelTypes } from '~/lib/consts'

const updateModelSlide = ref<InstanceType<typeof SlideOver> | null>(null)

const modelStore = useModelStore()

const selectedModelType: Ref<{ label: string, value: string } | null> = ref(null)

const schema = z.object({
  uuid: z.string().nonempty({ message: 'Required' }),
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  model_type: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  base_url: z
    .string()
    .nonempty({ message: 'Required' })
    .min(1)
    .max(255)
    .url({ message: 'Invalid URL' }),
  api_key: z.string().optional(),
  model_name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    uuid: '',
    name: '',
    model_type: '',
    base_url: '',
    api_key: '',
    model_name: '',
  },
})
const { isSubmitting, meta, setValues } = form

function open(model: LLMModel) {
  const modelType = model.model_type

  setValues({
    uuid: model.uuid,
    name: model.name,
    model_type: modelType,
    base_url: model.base_url!,
    api_key: '',
    model_name: model.model_name,
  })
  selectedModelType.value = ModelTypes.find((m) => m.value === modelType) || null

  updateModelSlide.value?.openSlide()
}

defineExpose({
  open
})

const updateModel = form.handleSubmit(async (values) => {
  try {
    await modelStore.update(values)
    updateModelSlide.value?.closeSlide()
    toast.success('Model updated')
  } catch (e: unknown) {
    setBackendErrors(form, e.errors)
    toast.error('Failed to update model')
  }
})

const disabled = computed(() => !meta.value.valid)
</script>
