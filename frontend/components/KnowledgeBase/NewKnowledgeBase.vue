<template>
  <BaseSheet
    title="Add Files to Knowledge Base"
    submit-text="Upload & Process"
    :on-submit="uploadAndProcess"
  >
    <template #trigger>
      <Button>Add to Knowledge Base</Button>
    </template>
    <div class="space-y-4">
      <SourceSelector v-model="selectedSourceValue" :sources="sources" />
      <div class="space-y-2">
        <div v-if="isFile" class="space-y-2">
          <Label for="upload_files" class="text-sm font-medium">
            Upload Files
          </Label>
          <FileUpload
            :max-files="1"
            @update:files="handleFileUpload"
          />
        </div>

        <UrlInput
          v-if="isUrl"
          v-model="urlInput"
          @add="addURL"
        />

        <TextInput
          v-if="isText"
          v-model="textInput"
          @add="addText"
        />
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
  </BaseSheet>
</template>
<script setup lang="ts">
import { Button } from '~/components/ui/button'
import SourceSelector from '~/components/KnowledgeBase/SourceSelector.vue'
import FileUpload from '~/components/KnowledgeBase/FileUpload.vue'
import UrlInput from '~/components/KnowledgeBase/UrlInput.vue'
import TextInput from '~/components/KnowledgeBase/TextInput.vue'
import BaseSheet from '~/components/BaseSheet.vue'
import Draft from '~/components/KnowledgeBase/Draft'
import { KB_SOURCES } from '~/lib/consts'
import { computed, ref } from 'vue'
import { useHttpClient } from '~/composables/useHttpClient'
import { toast } from 'vue-sonner'
import { useKBDraftStore } from '~/stores/kbDraft'
import { useApplicationsStore } from '~/stores/applications'


const appStore = useApplicationsStore()
const selectedApp = computed(() => appStore.selectedApplication)

const sources = KB_SOURCES
const selectedSourceValue = ref('file')
const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')

const textInput = ref('')
const urlInput = ref('')

const handleFileUpload = (files: File[]) => {
  kbDraft.setFiles(files)
}
const kbDraft = useKBDraftStore()
const emit = defineEmits(['knowledgeAdded'])

const addText = () => {
  if (textInput.value.trim()) {
    kbDraft.addText(textInput.value.trim())
    textInput.value = ''
  }
}

const addURL = () => {
  if (urlInput.value.trim()) {
    kbDraft.addUrl(urlInput.value.trim())
    urlInput.value = ''
  }
}

async function uploadAndProcess() {
  const formData = new FormData()

  kbDraft.items.forEach((item, index) => {
    formData.append(`items[${index}].type`, item.type)
    if (item.type === 'file') {
      formData.append(`items[${index}].file`, item.value)
    } else {
      formData.append(`items[${index}].value`, item.value)
    }
  })

  try {
    const { httpPostForm } = useHttpClient()
    await httpPostForm(
      `/applications/${selectedApp.value.uuid}/knowledge-bases/`,
      formData
    )
    kbDraft.clear()
    emit('knowledgeAdded', true)
    toast.success('Files uploaded successfully')
  } catch (err: any) {
    toast.error(err.message || 'Error uploading files')
    console.error('Error uploading:', err)
  }
}
</script>