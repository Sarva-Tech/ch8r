<template>
  <Accordion type="single" collapsible>
    <AccordionItem value="advanced-settings">
      <AccordionTrigger>Advanced Settings</AccordionTrigger>
      <AccordionContent class="space-y-4">
        <div class="space-y-2">
          <Label>Notification Profiles</Label>

          <div class="flex w-full gap-2 items-center">
            <MultiSelectComboBox
              v-model="selectedProfile"
              class="w-full"
              label="Select Profile"
              :options="notificationProfileOptions"
              placeholder="Notification Profiles"
            />
            <Button
              type="button"
              size="sm"
              variant="outline"
              class="flex-none h-10 w-10 flex items-center justify-center"
              aria-label="Create new notification profile"
              @click="toggleCreateForm"
            >
              <Plus class="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div v-if="showCreateForm" class="space-y-4 border p-4 rounded-md">

          <div class="flex justify-end">
            <Button> create</Button>
          </div>
        </div>
      </AccordionContent>
    </AccordionItem>
  </Accordion>
</template>
<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-vue-next'
import { MultiSelectComboBox } from '~/components/ui/multiselectcombobox'

const notificationProfileStore = useNotificationProfileStore()

const selectedNotificationProfiles = ref<(number | string)[]>([])
const notificationProfiles = computed(() => notificationProfileStore.profiles)


const showCreateForm = ref(false)


computed(() =>
  notificationProfiles.value
    .filter((p) => selectedNotificationProfiles.value.includes(p.id!))
    .map((p) => p.name),
)
const notificationProfileOptions = computed(() =>
  notificationProfiles.value.map((p) => ({ label: p.name, value: p.name })),
)

const toggleCreateForm = () => {
  showCreateForm.value = !showCreateForm.value
}
</script>
