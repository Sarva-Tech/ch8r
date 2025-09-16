<template>
  <SlideOver
    v-model:open="open"
    title="Update Knowledge Base"
    submit-text="Update & Process"
    :on-submit="updateKB"
  >
    <div class="space-y-4">
      <div class="space-y-2">
        <Label for="for_text" class="text-sm font-medium">Content</Label>
        <Textarea
          v-model="content"
          placeholder="Updated knowledge base content"
          class="max-h-100 overflow-y-auto resize-none"
        />
      </div>
    </div>
  </SlideOver>
</template>
<script setup lang="ts">
import SlideOver from '~/components/SlideOver.vue'
import { ref, defineExpose } from 'vue'
import type { KBTableRow } from '~/lib/types'

const open = ref(false)
const selectedKB = ref<KBTableRow | null>(null)
const content = ref('')

const kbStore = useKnowledgeBaseStore()

function openSlide(kb: KBTableRow) {
  selectedKB.value = kb
  content.value = selectedKB.value?.content || ''
  open.value = true
}

async function updateKB() {
  if (!selectedKB.value) return
  await kbStore.update(selectedKB.value?.uuid, content.value)
  open.value = false
}

defineExpose({ openSlide })
</script>
