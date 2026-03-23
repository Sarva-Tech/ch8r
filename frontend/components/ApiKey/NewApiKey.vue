<template>
  <SlideOver
    ref="newAPIKeySlideOver"
    title="Add New API Key"
  >
    <template #trigger>
      <C8Button
        label="Add API Key"
        :icon="Plus"
        @click="openSlideWithReset"
      />
    </template>

    <form
      class="space-y-5"
      @submit.prevent="createNewAPIKey"
    >
      <C8APIAlert :api-error="apiError" />

      <FormField
        v-slot="{ componentField }"
        name="name"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              API Key Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <div class="flex gap-2">
              <Input
                v-bind="componentField"
                placeholder="API Key Name"
                class="flex-1"
              />
              <C8Button
                variant="outline"
                size="icon"
                type="button"
                @click="generateUniqueAPIKeyName"
              >
                <Sparkles class="h-4 w-4" />
              </C8Button>
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField
        v-slot="{ componentField }"
        name="permissions"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Permissions
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <C8Combobox
              v-bind="componentField"
              v-model="selectedPermissions"
              :options="permissions"
              :multiple="true"
              placeholder="Select permissions"
              search-placeholder="Type to search"
              :allow-custom-values="false"
              @update:model-value="(value) => {
                selectedPermissions = value
                form.setFieldValue('permissions', value)
              }"
            />
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
        @click="createNewAPIKey"
      />
    </template>
  </SlideOver>

  <Dialog v-model:open="isCopyApiKeyDialogOpen">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Copy API Key</DialogTitle>
        <DialogDescription>Your API key is {{ newAPIKey }}</DialogDescription>
      </DialogHeader>

      <DialogFooter>
        <Button @click="copyApiKey">
          Copy And Close
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { Button } from '~/components/ui/button'
import SlideOver from '~/components/SlideOver.vue'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8Combobox from '~/components/C8Combobox.vue'
import { computed, ref, onMounted, watch } from 'vue'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { toast } from 'vue-sonner'
import { useUniqueName } from '~/composables/useUniqueName'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { Plus, Sparkles } from 'lucide-vue-next'

const newAPIKeySlideOver = ref<InstanceType<typeof SlideOver> | null>(null)
const apiKeyStore = useAPIKeyStore()
const { generateShortUniqueName } = useUniqueName()
const { apiError, handleError, clearError } = useApiErrorHandling()

const newAPIKey = ref('')
const isCopyApiKeyDialogOpen = ref(false)
const selectedPermissions = ref<string[]>([])

const permissions = [
  { value: 'read', label: 'Read', selected: false },
  { value: 'write', label: 'Write', selected: false },
  { value: 'delete', label: 'Delete', selected: false },
]

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  permissions: z.array(z.string()).min(1, { message: 'Required' }),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    name: '',
    permissions: [],
  },
})
const { isSubmitting } = form

onMounted(() => {
  resetFormToCustomDefaults()
})

const resetFormToCustomDefaults = () => {
  const uniqueName = generateShortUniqueName('API Key')
  selectedPermissions.value = []
  form.resetForm({
    values: {
      name: uniqueName,
      permissions: [],
    },
  })
}

const openSlideWithReset = () => {
  resetFormToCustomDefaults()
  newAPIKeySlideOver.value?.openSlide()
}

const generateUniqueAPIKeyName = () => {
  const uniqueName = generateShortUniqueName('API Key')
  form.setFieldValue('name', uniqueName)
}

watch(() => form.values.permissions, (newPermissions) => {
  if (JSON.stringify(newPermissions) !== JSON.stringify(selectedPermissions.value)) {
    selectedPermissions.value = newPermissions || []
  }
}, { deep: true })

const createNewAPIKey = form.handleSubmit(async (values) => {
  clearError()

  try {
    const response = await apiKeyStore.create({
      name: values.name,
      permissions: values.permissions
    })

    if (response?.api_key) {
      newAPIKey.value = response.api_key
      apiKeyStore.newAPIKey = response
      newAPIKeySlideOver.value?.closeSlide()
      isCopyApiKeyDialogOpen.value = true
      toast.success('API Key created')
    }
  } catch (error: unknown) {
    handleError(error, form)
  }
})

function copyApiKey() {
  if (newAPIKey.value) {
    navigator.clipboard.writeText(newAPIKey.value)
    isCopyApiKeyDialogOpen.value = false
  }
}

const disabled = computed(() => {
  const values = form.values
  return !(
    values.name?.trim()
    && (values.permissions && values.permissions.length > 0)
  )
})
</script>
