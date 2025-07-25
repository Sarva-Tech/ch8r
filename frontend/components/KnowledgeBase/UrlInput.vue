<template>
  <div class="space-y-2">
    <Label for="url_input" class="text-sm font-medium">
      <slot>URL</slot>
    </Label>
    <div class="flex gap-2">
      <Input
        v-model="localUrl"
        :placeholder="placeholder"
        class="flex-1"
        @keyup.enter="handleAdd"
      />
      <Button
        variant="secondary"
        :disabled="!isValidUrl"
        @click="handleAdd"
      >
        <slot name="button-text">Add URL</slot>
      </Button>
    </div>
    <p v-if="errorMessage" class="text-sm text-destructive">
      {{ errorMessage }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useKBDraftStore } from '~/stores/kbDraft'

const props = withDefaults(defineProps<{
  placeholder?: string
}>(), {
  placeholder: 'https://example.com'
})

const localUrl = ref('')
const errorMessage = ref('')
const kbDraft = useKBDraftStore()

const isValidUrl = computed(() => {
  try {
    new URL(localUrl.value)
    return true
  } catch {
    return false
  }
})

const handleAdd = () => {
  if (!isValidUrl.value) {
    errorMessage.value = 'Please enter a valid URL (e.g., https://example.com)'
    return
  }

  errorMessage.value = ''
  kbDraft.addUrl(localUrl.value)
  localUrl.value = ''
}
</script>