<template>
  <SlideOver
    ref="newAPIKeySlideOver"
    title="Create API Key"
  >
    <template #trigger>
      <C8Button label="Create API Key" />
    </template>
    <form class="space-y-5" @submit.prevent="createNewAPIKey">
      <FormField v-slot="{ componentField }" name="name">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              API Key Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input v-bind="componentField" placeholder="API Key Name" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="permissions">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Permissions
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <C8Multiselect
              v-bind="componentField"
              v-model="selectedPermissions"
              :options="permissions"
              :multiple="true"
              :preselect-first="false"
              placeholder="Select permissions"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>
    </form>
    <Dialog v-model:open="isCopyApiKeyDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Copy API Key</DialogTitle>
          <DialogDescription>Your API key is {{ newAPIKey }}</DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button @click="copyApiKey">Copy And Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <template #submitBtn>
      <C8Button
        label="Create"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="createNewAPIKey"
      />
    </template>
  </SlideOver>
</template>
<script setup lang="ts">
import { Button } from '~/components/ui/button'
import SlideOver from '~/components/SlideOver.vue'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { computed, ref } from 'vue'
import type { SelectOption } from '~/lib/types'
import { z } from 'zod'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { toast } from 'vue-sonner'
import { setBackendErrors } from '~/lib/utils'

const newAPIKeySlideOver = ref<InstanceType<typeof SlideOver> | null>(
  null,
)

const apiKeyStore = useAPIKeyStore()
const newAPIKey = ref('')
const isCopyApiKeyDialogOpen = ref(false)

const selectedPermissions = ref<SelectOption[]>([])
const permissions = [
  { value: 'read', label: 'Read', selected: false },
  { value: 'write', label: 'Write', selected: false },
  { value: 'delete', label: 'Delete', selected: false },
]

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  permissions: z.array(
    z.object({
      value: z.string().nonempty(),
      label: z.string().nonempty(),
      selected: z.boolean()
    })
  ).min(1, { message: 'Required' }),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    name: '',
    permissions: [],
  },
})

const { isSubmitting, meta } = form

const createNewAPIKey = form.handleSubmit(async (values) => {
  try {
    const response = await apiKeyStore.create({
      name: values.name,
      permissions: values.permissions?.map(s => s.value)
    })

    if(response?.api_key) {
      apiKeyStore.newAPIKey = response
      newAPIKeySlideOver.value?.closeSlide()
      toast.success('API Key created')
    }
  } catch (e: unknown) {
    setBackendErrors(form, e.errors)
  }
})

function copyApiKey() {
  if (newAPIKey.value) {
    navigator.clipboard.writeText(newAPIKey.value)
    isCopyApiKeyDialogOpen.value = false
  }
}

const disabled = computed(() =>
  !meta.value.valid
)
</script>
