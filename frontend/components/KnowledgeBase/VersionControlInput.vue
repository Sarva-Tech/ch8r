<template>
  <div class="space-y-4">
    <div
      v-if="!vcIntegration"
      class="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
    >
      No Version Control integration configured for this application.
      Open app settings → Integrations tab to configure one.
    </div>

    <div
      v-else-if="!configuredRepo"
      class="rounded-lg border border-amber-500/50 bg-amber-50 dark:bg-amber-950/20 p-3 text-sm text-amber-700 dark:text-amber-400"
    >
      No repository configured for Version Control.
      Open app settings → Integrations tab to set a repository.
    </div>

    <template v-else>
      <div class="rounded-lg border bg-muted/40 p-3 space-y-1">
        <div class="flex items-center gap-2 text-sm">
          <component
            :is="useIntegrationIcon(vcIntegration.integration.provider).value"
            v-if="useIntegrationIcon(vcIntegration.integration.provider).value"
            class="h-4 w-4 shrink-0 text-muted-foreground"
          />
          <span class="text-muted-foreground">Using</span>
          <span class="font-medium">{{ vcIntegration.integration.name }}</span>
          <span class="text-xs text-muted-foreground capitalize">({{ vcIntegration.integration.provider }})</span>
        </div>
        <div class="flex items-center gap-2 text-sm">
          <FolderGit2 class="h-4 w-4 shrink-0 text-muted-foreground" />
          <span class="font-mono text-xs">{{ configuredRepo }}</span>
        </div>
      </div>

      <div class="space-y-2">
        <Label class="text-sm font-medium">Ingest Since (Optional)</Label>
        <C8Input
          v-model="since"
          type="datetime-local"
          placeholder=""
          :disabled="loading"
        />
        <p class="text-xs text-muted-foreground">
          Leave empty to ingest all data from the repository.
        </p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { VCIngestionRequest } from '~/types/version_control'
import { useIntegrationIcon } from '~/composables/useIntegrationIcon'
import { FolderGit2 } from 'lucide-vue-next'
import { useAppIntegrationStore } from '~/stores/appIntegration'

withDefaults(defineProps<{ loading?: boolean }>(), { loading: false })

const emit = defineEmits<{
  update: [data: VCIngestionRequest | null]
}>()

const appStore = useApplicationsStore()
const appIntegrationStore = useAppIntegrationStore()

const since = ref('')

const vcIntegration = computed(() =>
  appIntegrationStore.appIntegrations.find(ai => ai.integration_type === 'version_control'),
)

const configuredRepo = computed(() =>
  (vcIntegration.value?.metadata?.repo as string) ?? '',
)

onMounted(async () => {
  const appUuid = appStore.selectedApplication?.uuid
  if (appUuid) {
    await appIntegrationStore.load(appUuid)
  }
})

const isValid = computed(() =>
  !!vcIntegration.value && !!configuredRepo.value,
)

watch([since, vcIntegration], () => {
  const appUuid = appStore.selectedApplication?.uuid
  if (isValid.value && appUuid) {
    const [owner, repo] = configuredRepo.value.split('/')
    emit('update', {
      owner: owner?.trim() ?? '',
      repo: repo?.trim() ?? '',
      application_uuid: appUuid,
      since: since.value ? new Date(since.value).toISOString() : undefined,
    })
  } else {
    emit('update', null)
  }
}, { immediate: true })
</script>
