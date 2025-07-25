<template>
  <div class="space-y-2">
    <Label for="for_text" class="text-sm font-medium">Text</Label>
    <Textarea
      v-model="localText"
      :placeholder="placeholder"
      class="max-h-100 overflow-y-auto resize-none"
    />
    <div class="flex justify-end">
      <Button
        variant="secondary"
        :disabled="!localText.trim()"
        @click="handleAdd"
      >
        Add Text
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useKBDraftStore } from '~/stores/kbDraft'

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Enter your text here'
  }
})

const localText = ref('')
const kbDraft = useKBDraftStore()

const handleAdd = () => {
  if (localText.value.trim()) {
    kbDraft.addText(localText.value.trim())
    localText.value = ''
  }
}
</script>