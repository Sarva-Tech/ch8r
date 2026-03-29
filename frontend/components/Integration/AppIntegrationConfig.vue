<template>
  <div class="space-y-6">
    <div
      v-for="type in SUPPORTED_INTEGRATION_TYPES"
      :key="type.id"
      class="space-y-4"
    >
      <h3 class="text-sm font-semibold">
        {{ type.label }}
      </h3>

      <template v-if="integrationStore.integrations.length === 0">
        <p class="text-sm text-muted-foreground">
          No integrations connected. Connect one in
          <NuxtLink
            to="/settings/integrations"
            class="underline"
          >
            Settings → Integrations
          </NuxtLink>.
        </p>
      </template>

      <template v-else>
        <C8APIAlert :api-error="sectionErrors[type.id] ?? null" />

        <C8Select
          v-model="sectionState[type.id].integrationUuid"
          label="Integration"
          placeholder="Select an integration"
          :options="integrationOptions"
        />

        <div class="space-y-2">
          <label class="text-sm font-medium">Repository</label>
          <Input
            v-model="sectionState[type.id].repo"
            placeholder="owner/repo"
          />
        </div>

        <C8Button
          label="Save"
          :loading="sectionState[type.id].saving"
          @click="save(type.id)"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import { useIntegrationStore } from '~/stores/integration'
import { useAppIntegrationStore } from '~/stores/appIntegration'
import C8Select from '~/components/C8Select.vue'
import { Input } from '~/components/ui/input'
import C8Button from '~/components/C8Button.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'

const SUPPORTED_INTEGRATION_TYPES = [
  { id: 'version_control', label: 'Version Control' },
  { id: 'project_management', label: 'Project Management' },
] as const

type IntegrationTypeId = typeof SUPPORTED_INTEGRATION_TYPES[number]['id']

const props = defineProps<{
  applicationUuid: string
}>()

const integrationStore = useIntegrationStore()
const appIntegrationStore = useAppIntegrationStore()

const sectionState = ref<Record<IntegrationTypeId, { integrationUuid: string | null; repo: string; saving: boolean }>>({
  version_control: { integrationUuid: null, repo: '', saving: false },
  project_management: { integrationUuid: null, repo: '', saving: false },
})

const sectionErrors = ref<Record<string, unknown>>({
  version_control: null,
  project_management: null,
})

const integrationOptions = computed(() =>
  integrationStore.integrations.map(i => ({
    label: i.name || i.provider,
    value: i.uuid,
  })),
)

function populateFromExisting() {
  for (const type of SUPPORTED_INTEGRATION_TYPES) {
    const existing = appIntegrationStore.appIntegrations.find(
      ai => ai.integration_type === type.id,
    )
    if (existing) {
      sectionState.value[type.id].integrationUuid = existing.integration.uuid
      sectionState.value[type.id].repo = (existing.metadata?.repo as string) ?? ''
    }
  }
}

onMounted(async () => {
  await Promise.all([
    appIntegrationStore.load(props.applicationUuid),
    integrationStore.load(),
  ])
  populateFromExisting()
})

async function save(typeId: IntegrationTypeId) {
  const state = sectionState.value[typeId]
  sectionErrors.value[typeId] = null
  state.saving = true

  const { handleError, apiError } = useApiErrorHandling()

  try {
    await appIntegrationStore.create(props.applicationUuid, {
      integration_uuid: state.integrationUuid,
      integration_type: typeId,
      metadata: { repo: state.repo },
    })
    toast.success('Integration saved')
  }
  catch (error: unknown) {
    handleError(error)
    sectionErrors.value[typeId] = apiError.value
  }
  finally {
    state.saving = false
  }
}
</script>
