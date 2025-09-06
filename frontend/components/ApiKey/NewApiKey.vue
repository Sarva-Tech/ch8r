<template>
  <Button variant="secondary" class="mr-4" @click="openHelpDialog">Help</Button>

  <SlideOver
    ref="apikeySlideOver"
    title="Create API Key"
    submit-text="Create"
    :on-submit="handleCreate"
    :loading="isSubmitting"
    :disabled="disabled"
  >
    <template #trigger>
      <Button>Create API Key</Button>
    </template>

    <form class="space-y-4">
      <FormField v-slot="{ field }" name="name">
        <FormItem>
          <FormLabel class="flex items-center gap-1">
            API Key Name <RequiredLabel />
          </FormLabel>
          <FormControl>
            <Input v-bind="field" id="name" placeholder="Enter API Key name" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ field }" name="permissions">
        <FormItem>
          <FormLabel>
            Permissions
            <RequiredLabel />
          </FormLabel>
          <FormControl>
            <MultiSelectComboBox
              v-bind="field"
              :options="permissions"
              placeholder="Select permissions"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <Dialog v-model:open="isCopyApiKeyDialogOpen">
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Copy API Key</DialogTitle>
            <DialogDescription>
              Your API key is {{ apiKey }}
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button @click="copyApiKey">Copy And Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </form>
  </SlideOver>

  <Dialog v-model:open="isHelpDialogOpen">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Sample usage of API Key</DialogTitle>
        <DialogDescription>
          <div class="w-full">
            curl -X GET -H 'x-api-key: your-api-key' https://example.com
          </div>
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button @click="closeHelpDialog">Close</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button } from '~/components/ui/button'
import { MultiSelectComboBox } from '~/components/ui/multiselectcombobox'
import SlideOver from '~/components/SlideOver.vue'
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '~/components/ui/dialog'

import { useAPIKeyStore } from '~/stores/apiKey'
import { toast } from 'vue-sonner'

const apiKeyStore = useAPIKeyStore()

const apikeySlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const { isSubmitting, meta, validate } = apiKeyStore.getFormInstance()

const apiKey = ref('')
const isCopyApiKeyDialogOpen = ref(false)
const isHelpDialogOpen = ref(false)

const permissions = [
  { value: 'read', label: 'Read' },
  { value: 'write', label: 'Write' },
  { value: 'delete', label: 'Delete' },
]

onMounted(() => {
  validate()
})
async function handleCreate() {
  try {
    await apiKeyStore.create()
    apikeySlideOver.value?.closeSlide()
    toast.success('Api key created created')
  } catch (e: never) {
    apiKeyStore.setBackendErrors(e.errors)
  }
}

function copyApiKey() {
  navigator.clipboard.writeText(apiKey.value)
  isCopyApiKeyDialogOpen.value = false
}

function openHelpDialog() {
  isHelpDialogOpen.value = true
}

function closeHelpDialog() {
  isHelpDialogOpen.value = false
}

const disabled = computed(() => !meta.value.valid)
</script>
