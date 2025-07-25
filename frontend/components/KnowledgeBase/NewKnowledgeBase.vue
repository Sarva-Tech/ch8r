<template>
  <BaseSheet
    title="Add Files to Knowledge Base"
    submit-text="Upload & Process"
    :on-submit="processKB"
  >
    <template #trigger>
      <Button>Add to Knowledge Base</Button>
    </template>
    <div class="space-y-4">
      <div class="space-y-2">
        <Label for="kb_source" class="text-sm font-medium">
          Knowledge Base Source
        </Label>
        <Select v-model="selectedSourceValue">
          <SelectTrigger class="w-full">
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              <component
                :is="selectedSource.icon"
                v-if="selectedSource"
                class="w-4 h-4"
              />
              <span>
                {{ selectedSource?.label || 'Knowledge Source' }}
              </span>
            </div>
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem
                v-for="source in sources"
                :key="source.value"
                :value="source.value"
              >
                <component :is="source.icon" class="w-4 h-4" />
                {{ source.label }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>
      <div class="space-y-2">
        <div v-if="isFile" class="space-y-2">
          <Label for="upload_files" class="text-sm font-medium">
            Upload Files
          </Label>
          <FileUpload @update:files="kbDraft.setFiles" />
        </div>
        <div v-if="isUrl" class="space-y-2">
          <Label for="for_url" class="text-sm font-medium"> URL </Label>
          <Input
            v-model="urlInput"
            type="url"
            placeholder="URL (https://sarvalekh.com)"
          />
          <div class="flex justify-end">
            <Button variant="secondary" @click="addURL">Add URL</Button>
          </div>
        </div>
        <div v-if="isText" class="space-y-2">
          <Label for="for_text" class="text-sm font-medium"> Text </Label>
          <Textarea
            v-model="textInput"
            placeholder="Provide a complete overview of your application."
            class="max-h-100 overflow-y-auto resize-none"
          />
          <div class="flex justify-end">
            <Button variant="secondary" @click="addText">Add Text</Button>
          </div>
        </div>
      </div>
      <Draft
        v-for="item in kbDraft.items"
        :key="item.id"
        :item="item"
        @remove="kbDraft.remove"
      />
    </div>
  </BaseSheet>
</template>
<script setup lang="ts">
import { Button } from '~/components/ui/button'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import Draft from '~/components/KnowledgeBase/Draft.vue'
import { KB_SOURCES } from '~/lib/consts'
import { computed } from 'vue'

const sources = KB_SOURCES
const selectedSourceValue = ref('file')
const selectedSource = computed(() =>
  sources.find((s) => s.value === selectedSourceValue.value),
)

const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')

const textInput = ref('')
const urlInput = ref('')

const kbDraft = useKBDraftStore()
const kbStore = useKnowledgeBaseStore()

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

async function processKB() {
  await kbStore.process()
}
</script>
