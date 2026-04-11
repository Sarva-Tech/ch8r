<template>
  <SlideOver
    ref="newKBSlideOver"
    title="Add to Knowledge Base"
  >
    <template #trigger>
      <C8Button
        label="Add to Knowledge Base"
        :icon="Plus"
      />
    </template>
    <div class="space-y-4">
      <C8APIAlert :api-error="apiError" />
      <SourceSelector
        v-model="selectedSourceValue"
        :sources="sources"
      />
      <div class="space-y-2">
        <div
          v-if="isFile"
          class="space-y-2"
        >
          <Label
            for="upload_files"
            class="text-sm font-medium"
          >
            Upload Files
            <RequiredLabel />
          </Label>
          <FileUpload @update:files="kbDraft.setFiles" />
        </div>
        <template v-if="isVersionControl">
          <template v-if="!hasVCIntegration">
            <div class="rounded-md border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950 p-3 space-y-3">
              <p class="text-sm font-medium text-amber-800 dark:text-amber-200">
                Connect a version control integration
              </p>
              <ConnectIntegration
                :inline="true"
                :provider="vcProvider"
                @connected="onVCIntegrationConnected"
              />
            </div>
          </template>

          <template v-else-if="!hasVCAppIntegration">
            <div class="rounded-md border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950 p-3 space-y-3">
              <ConfigureIntegration
                :config="vcIntegrationConfig"
                :inline="true"
              />
            </div>
          </template>

          <VersionControlInput
            v-else
            :loading="loading"
            @update="handleVCUpdate"
          />
        </template>
        <UrlInput
          v-if="isUrl"
          :application-uuid="application.uuid"
        />
        <TextInput v-if="isText" />
      </div>
      <div class="space-y-2">
        <Draft
          v-for="item in kbDraft.items"
          :key="item.id"
          :item="item"
          @remove="kbDraft.remove"
        />
      </div>
    </div>

    <template #submitBtn>
      <C8Button
        label="Upload & Process"
        :disabled="disabled"
        :loading="loading"
        @click="processKB"
      />
    </template>
  </SlideOver>
</template>

<script setup lang="ts">
import SourceSelector from '~/components/KnowledgeBase/SourceSelector.vue'
import FileUpload from '~/components/FileUpload.vue'
import UrlInput from '~/components/KnowledgeBase/UrlInput.vue'
import TextInput from '~/components/KnowledgeBase/TextInput.vue'
import VersionControlInput from '~/components/KnowledgeBase/VersionControlInput.vue'
import SlideOver from '~/components/SlideOver.vue'
import Draft from '~/components/KnowledgeBase/Draft.vue'
import C8Empty from '~/components/C8Empty.vue'
import ConnectIntegration from '~/components/Integration/ConnectIntegration.vue'
import ConfigureIntegration from '~/components/App/ConfigureIntegration.vue'
import { KB_SOURCES } from '~/lib/consts'
import { computed, ref, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { Plus, Inbox } from 'lucide-vue-next'
import type { VCIngestionRequest } from '~/types/version_control'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import C8APIAlert from '~/components/C8APIAlert.vue'
import { useIntegrationStore } from '~/stores/integration'
import { useAppIntegrationStore } from '~/stores/appIntegration'

const props = defineProps<{
  application: {
    uuid: string
  }
}>()

const newKBSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const loading = ref(false)
const sources = KB_SOURCES
const selectedSourceValue = ref('file')
const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')
const isVersionControl = computed(() => selectedSourceValue.value === 'github')

const kbDraft = useKBDraftStore()
const kbStore = useKnowledgeBaseStore()
const vcStore = useVersionControlStore()
const integrationStore = useIntegrationStore()
const appIntegrationStore = useAppIntegrationStore()
const appStore = useApplicationsStore()

const hasVCIntegration = computed(() =>
  integrationStore.integrations.some(i => i.supported_types?.includes('version_control')),
)
const hasVCAppIntegration = computed(() =>
  appIntegrationStore.appIntegrations.some(i => i.integration_type === 'version_control'),
)

const vcIntegrationConfig = {
  id: 'version_control',
  title: 'Version Control',
  description: 'Select the version control integration and repository to connect.',
  requiresRepo: true,
  successMessage: 'Version control integration configured',
}

const vcProvider = computed(() =>
  integrationStore.supportedIntegrations.find(p => p.supported_types?.includes('version_control')),
)

async function onVCIntegrationConnected() {
  await integrationStore.load()
}

const vcData = ref<VCIngestionRequest | null>(null)

const { apiError, handleError, clearError } = useApiErrorHandling()

onMounted(async () => {
  await Promise.allSettled([
    integrationStore.load(),
    appStore.selectedApplication?.uuid
      ? appIntegrationStore.load(appStore.selectedApplication.uuid)
      : Promise.resolve(),
  ])
})

async function processKB() {
  loading.value = true
  clearError()
  try {
    if (isVersionControl.value && vcData.value) {
      await vcStore.ingestRepository(vcData.value)
      newKBSlideOver.value?.closeSlide()
      toast.success('Repository ingestion started. The knowledge base will update when complete.')
      kbDraft.clear()
      vcData.value = null
      await kbStore.load()
    } else {
      await kbStore.process()
      newKBSlideOver.value?.closeSlide()
      toast.success('Knowledge base processing started')
      kbDraft.clear()
    }
  } catch (e: unknown) {
    handleError(e)
  } finally {
    loading.value = false
  }
}

function handleVCUpdate(data: VCIngestionRequest | null) {
  vcData.value = data
}

const disabled = computed(() => {
  if (isVersionControl.value) {
    if (!hasVCIntegration.value || !hasVCAppIntegration.value) return true
    return !vcData.value
  }
  return !kbDraft.hasDrafts
})
</script>
