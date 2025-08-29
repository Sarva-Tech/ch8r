<template>

  <Button variant="secondary" class="mr-4" @click="openHelpDialog">Help</Button>
  <SlideOver
    title="Create API Key"
    submit-text="Create"
    :on-submit="createApiKey"
  >
    <template #trigger>
      <Button>Create API Key</Button>
    </template>
    <div class="space-y-4">
      <div class="space-y-2">
        <div class="space-y-2">
          <Label for="name" class="text-sm font-medium">
            API Key Name
          </Label>
          <Input id="name" v-model="apiKeyName"/>
        </div>
        <div class="space-y-2">
          <MultiSelectComboBox
              class="w-full"
            v-model="selectedPermissions"
            label="Select Permissions"
            :options="permissions"
            placeholder="Permissions"
          />
        </div>
      </div>
    </div>
    <Dialog v-model:open="isCopyApiKeyDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Copy API Key</DialogTitle>
          <DialogDescription>Your API key is {{ apiKey }}</DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button @click="copyApiKey">Copy And Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </SlideOver>
  <Dialog v-model:open="isHelpDialogOpen">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Sample usage of API Key</DialogTitle>
        <DialogDescription>
          <div class="bg-gray w-full">
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
import {Button} from '~/components/ui/button'
import {MultiSelectComboBox} from '~/components/ui/multiselectcombobox'
import SlideOver from '~/components/SlideOver.vue'

const apiKeyName = ref('')

const apiKeyStore = useAPIKeyStore()
let apiKey
const isCopyApiKeyDialogOpen = ref(false)
const isHelpDialogOpen = ref(false)

const selectedPermissions = ref<string[]>([])
const permissions = [
  { value: 'read', label: 'Read' },
  { value: 'write', label: 'Write' },
  { value: 'delete', label: 'Delete' },
]
async function createApiKey() {
  apiKey = await apiKeyStore.create({
    name: apiKeyName.value,
    permissions: selectedPermissions.value?.map(s => s.value)
  })
  isCopyApiKeyDialogOpen.value = true
}

function copyApiKey() {
  navigator.clipboard.writeText(apiKey)
  isCopyApiKeyDialogOpen.value = false
}

function openHelpDialog() {
  isHelpDialogOpen.value = true
}

function closeHelpDialog() {
  isHelpDialogOpen.value = false
}
</script>
