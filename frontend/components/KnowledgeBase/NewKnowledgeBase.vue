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
        <VersionControlInput
          v-if="isVersionControl"
          :loading="loading"
          @update="handleVCUpdate"
        />
        <UrlInput v-if="isUrl" :application-uuid="application.uuid" />
        <TextInput v-if="isText" />
      </div>
      <div class="space-y-2">
        <Draft
          v-for="item in kbDraft.items"
          :key="item.id"
          :item="item"
          @remove="kbDraft.remove"
        />
        <C8Empty
          v-if="kbDraft.items.length === 0 && !isVersionControl"
          :icon="Inbox"
          title="No items selected"
          description="Add files, URLs, or text to upload to your knowledge base."
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
import { KB_SOURCES } from '~/lib/consts'
import { computed, ref, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { Plus, Inbox } from 'lucide-vue-next'
import type { VCIngestionRequest } from '~/types/version_control'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import C8APIAlert from '~/components/C8APIAlert.vue'

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

const vcData = ref<VCIngestionRequest | null>(null)

const { apiError, handleError, clearError } = useApiErrorHandling()

onMounted(async () => {
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
    return !vcData.value
  }
  return !kbDraft.hasDrafts
})
</script>
