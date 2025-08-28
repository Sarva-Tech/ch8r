<template>
  <SlideOver
    title="Add Files to Knowledge Base"
    submit-text="Upload & Process"
    :on-submit="processKB"
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
          <FileUpload @update:files="kbDraft.setFiles" />
        </div>
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
  </SlideOver>
</template>
<script setup lang="ts">
import { Button } from '~/components/ui/button'
import SourceSelector from '~/components/KnowledgeBase/SourceSelector.vue'
import FileUpload from '~/components/FileUpload.vue'
import UrlInput from '~/components/KnowledgeBase/UrlInput.vue'
import TextInput from '~/components/KnowledgeBase/TextInput.vue'
import SlideOver from '~/components/SlideOver.vue'
import Draft from '~/components/KnowledgeBase/Draft.vue'
import { KB_SOURCES } from '~/lib/consts'
import { computed } from 'vue'

const sources = KB_SOURCES
const selectedSourceValue = ref('file')
const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')

const kbDraft = useKBDraftStore()
const kbStore = useKnowledgeBaseStore()


async function processKB() {
  await kbStore.process()
}
</script>
