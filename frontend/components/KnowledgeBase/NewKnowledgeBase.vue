<template>
  <SlideOver
    ref="newKBSlideOver"
    title="Add to Knowledge Base"
  >
    <template #trigger>
      <C8Button label="Add to Knowledge Base" />
    </template>
    <div class="space-y-4">
      <SourceSelector v-model="selectedSourceValue" :sources="sources" />
      <div class="space-y-2">
        <div v-if="isFile" class="space-y-2">
          <Label for="upload_files" class="text-sm font-medium">
            Upload Files
            <RequiredLabel />
          </Label>
          <FileUpload @update:files="kbDraft.setFiles" />
        </div>
        <GitHubInput v-if="isGitHub" :loading="loading" @update="handleGitHubUpdate" />
        <UrlInput v-if="isUrl" />
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
import GitHubInput from '~/components/KnowledgeBase/GitHubInput.vue'
import SlideOver from '~/components/SlideOver.vue'
import Draft from '~/components/KnowledgeBase/Draft.vue'
import { KB_SOURCES } from '~/lib/consts'
import { computed, ref, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { setBackendErrors } from '~/lib/utils'
import type { GitHubIngestionRequest } from '~/types/github'

const newKBSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const loading = ref(false)
const sources = KB_SOURCES
const selectedSourceValue = ref('file')
const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')
const isGitHub = computed(() => selectedSourceValue.value === 'github')

const kbDraft = useKBDraftStore()
const kbStore = useKnowledgeBaseStore()
const githubStore = useGitHubStore()
const integrationStore = useIntegrationStore()

const githubData = ref<GitHubIngestionRequest | null>(null)

onMounted(async () => {
  try {
    await integrationStore.loadAppIntegrations(useRoute().params.appId as string)
  } catch (error) {
    console.error('Failed to load integrations:', error)
    toast.error('Failed to load integration options')
  }
})

async function processKB() {
  loading.value = true
  try {
    if (isGitHub.value && githubData.value) {
      const response = await githubStore.ingestRepository(githubData.value)
      newKBSlideOver.value?.closeSlide()
      toast.success('GitHub repository ingestion started. The knowledge base will update when complete.')
      kbDraft.clear()
      githubData.value = null
      await kbStore.load()
    } else {
      await kbStore.process()
      newKBSlideOver.value?.closeSlide()
      toast.success('Knowledge base processing started')
      kbDraft.clear()
    }
  } catch (e: unknown) {
    toast.error('Failed to process knowledge base')
  } finally {
    loading.value = false
  }
}

function handleGitHubUpdate(data: GitHubIngestionRequest | null) {
  githubData.value = data
}

const disabled = computed(() => {
  if (isGitHub.value) {
    return !githubData.value
  }
  return !kbDraft.hasDrafts
})
</script>
