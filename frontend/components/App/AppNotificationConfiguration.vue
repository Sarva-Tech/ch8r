<template>
  <Card>
    <CardHeader>
      <CardTitle>Notifications</CardTitle>
      <CardDescription>
        Select notification profiles to receive alerts during smart escalation.
      </CardDescription>
    </CardHeader>
    <CardContent>
      <C8Loader v-if="initialLoading" container-class="flex justify-center py-4" />

      <div v-else-if="notificationStore.profiles.length === 0" class="text-sm text-muted-foreground py-2">
        No notification profiles found. Create one in
        <NuxtLink to="/settings/notification-profile" class="underline text-primary">
          Settings → Notifications
        </NuxtLink>.
      </div>

      <div v-else class="space-y-4">
        <C8APIAlert :api-error="apiError" />

        <div v-if="linkedProfiles.length > 0" class="space-y-2">
          <label class="text-sm font-medium">Active Profiles</label>
          <div class="space-y-2">
            <div
              v-for="profile in linkedProfiles"
              :key="profile.uuid"
              class="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm"
            >
              <div class="flex items-center gap-2">
                <component :is="getIcon(profile.type)" class="w-4 h-4 text-muted-foreground" />
                <span class="font-medium">{{ profile.name }}</span>
                <Badge variant="secondary" class="text-xs capitalize">{{ profile.type }}</Badge>
              </div>
              <Button
                variant="ghost"
                size="icon"
                class="h-7 w-7 text-muted-foreground hover:text-destructive"
                :disabled="processing"
                @click="removeProfile(profile.uuid!)"
              >
                <X class="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        <C8EmptyState
          v-else
          :icon="BellOff"
          title="No profiles linked"
          description="Add a notification profile below to start receiving alerts."
          class="py-8"
        />

        <div v-if="availableOptions.length > 0" class="flex items-end gap-2">
          <C8Select
            v-model="selectedUuid"
            label="Add Notification Profile"
            :options="availableOptions"
            placeholder="Select a profile to add..."
            container-class="flex-1"
          />
          <C8Button
            label="Add"
            :disabled="!selectedUuid || processing"
            :loading="processing"
            @click="addProfile"
          />
        </div>

        <p v-else-if="linkedProfiles.length > 0" class="text-xs text-muted-foreground">
          All available profiles are already linked.
        </p>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { toast } from 'vue-sonner'
import { computed, onMounted, ref } from 'vue'
import { Bell, BellOff, MessageSquare, Slack, X } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import C8Select from '~/components/C8Select.vue'
import C8Button from '~/components/C8Button.vue'
import C8Loader from '~/components/C8Loader.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8EmptyState from '~/components/C8EmptyState.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import type { NotificationProfile } from '~/stores/notificationProfile'

const appConfigStore = useAppConfigurationStore()
const notificationStore = useNotificationProfileStore()

const initialLoading = ref(false)
const processing = ref(false)
const selectedUuid = ref<string>('')
const { apiError, handleError, clearError } = useApiErrorHandling()

const linkedUuids = computed<string[]>(() =>
  (appConfigStore.notifications ?? [])
    .filter((n: NotificationProfile) => n.is_enabled)
    .map((n: NotificationProfile) => n.uuid!)
    .filter(Boolean),
)

const linkedProfiles = computed<NotificationProfile[]>(() =>
  (appConfigStore.notifications ?? []).filter((n: NotificationProfile) => n.is_enabled),
)

const availableOptions = computed(() =>
  notificationStore.profiles
    .filter(p => !linkedUuids.value.includes(p.uuid!))
    .map(p => ({ label: p.name, value: p.uuid ?? '' })),
)

function getIcon(type: string) {
  switch (type.toLowerCase()) {
    case 'slack': return Slack
    case 'discord': return MessageSquare
    default: return Bell
  }
}

onMounted(async () => {
  initialLoading.value = true
  try {
    await Promise.all([notificationStore.load(), appConfigStore.initialize()])
  } catch {
    toast.error('Failed to load notification profiles')
  } finally {
    initialLoading.value = false
  }
})

async function addProfile() {
  if (!selectedUuid.value) return

  if (linkedUuids.value.includes(selectedUuid.value)) {
    toast.error('This profile is already linked to this app.')
    return
  }

  clearError()
  processing.value = true
  try {
    await appConfigStore.saveNotifications([...linkedUuids.value, selectedUuid.value])
    selectedUuid.value = ''
    toast.success('Notification profile added')
  } catch (e: unknown) {
    handleError(e)
  } finally {
    processing.value = false
  }
}

async function removeProfile(uuid: string) {
  clearError()
  processing.value = true
  try {
    await appConfigStore.saveNotifications(linkedUuids.value.filter(u => u !== uuid))
    toast.success('Notification profile removed')
  } catch (e: unknown) {
    handleError(e)
  } finally {
    processing.value = false
  }
}
</script>
