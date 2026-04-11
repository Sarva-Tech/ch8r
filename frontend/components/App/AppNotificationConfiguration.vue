<template>
  <div class="w-full space-y-2">
    <C8Loader
      v-if="loading"
      container-class="flex justify-center items-center py-12"
    />

    <C8Empty
      v-else-if="notifications.length === 0"
      :icon="Bell"
      title="No notification profiles"
      description="Add a notification profile to receive alerts during escalation"
    >
      <template #action>
        <NewNotificationProfile @created="onNotificationCreated" />
      </template>
    </C8Empty>

    <template v-else>
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewNotificationProfile @created="onNotificationCreated" />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>
            Configure your notifications here so that you can receive alerts
            during smart escalation.
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-2">
          <C8Multiselect
            v-model="selectedNotifications"
            :options="notifications"
            :multiple="true"
            :preselect-first="false"
            label="Select notification profiles"
            placeholder="Select notification profiles"
          />
        </CardContent>
        <CardFooter class="flex justify-end">
          <C8Button
            label="Save"
            :disabled="processing"
            :loading="processing"
            @click="configureNotifications"
          />
        </CardFooter>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { toast } from 'vue-sonner'
import { computed, ref } from 'vue'
import { Bell } from 'lucide-vue-next'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import NewNotificationProfile from '~/components/notification/NewNotificationProfile.vue'
import C8Empty from '~/components/C8Empty.vue'
import C8Loader from '~/components/C8Loader.vue'
import type { SelectOption } from '~/lib/types'

const appConfigStore = useAppConfigurationStore()
const processing = ref(false)
const notifications = computed(() =>
  appConfigStore.notifications.map(n => ({
    label: n.name ?? '',
    value: n.uuid ?? '',
    selected: n.is_enabled ?? false,
  })),
)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await appConfigStore.initialize()
  } catch (e: unknown) {
    toast.error('Failed to load app configuration')
  } finally {
    loading.value = false
  }
})

const selectedNotifications = ref<SelectOption[]>([])
watch(
  notifications,
  (newNotifications) => {
    selectedNotifications.value = newNotifications.filter(n => n.selected)
  },
  { immediate: true },
)

async function configureNotifications() {
  processing.value = true

  try {
    await appConfigStore.saveNotifications(selectedNotifications.value)
    toast.success('Notifications configured')
  } catch (e: unknown) {
    toast.error(e?.message || 'Error configuring notifications')
    console.error(e)
  } finally {
    processing.value = false
  }
}

async function onNotificationCreated() {
  await appConfigStore.initialize()
}
</script>
