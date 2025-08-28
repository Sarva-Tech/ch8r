<template>
  <SlideOver
    title="Create Api Key"
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
            v-model="selectedPermissions"
            label="Select Permissions"
            :options="permissions"
          />
        </div>
      </div>
    </div>
  </SlideOver>
</template>
<script setup lang="ts">
import { Button } from '~/components/ui/button'
import { MultiSelectComboBox } from '~/components/ui/multiselectcombobox'
import SlideOver from '~/components/SlideOver.vue'

const apiKeyName = ref('')

const apiKeyStore = useAPIKeyStore()

const selectedPermissions = ref<string[]>([])
const permissions = [
  { value: 'read', label: 'Read' },
  { value: 'write', label: 'Write' },
  { value: 'delete', label: 'Delete' },
]
async function createApiKey() {
  await apiKeyStore.create({
    name: apiKeyName.value,
    permissions: selectedPermissions.value?.map(s => s.value)
  })
}
</script>
