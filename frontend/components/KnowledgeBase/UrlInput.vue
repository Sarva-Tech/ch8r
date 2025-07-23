<template>
  <div class="space-y-2">
    <Label for="url_input" class="text-sm font-medium">
      <slot>URL</slot>
    </Label>
    <div class="flex gap-2">
      <Input
        :model-value="modelValue"
        :placeholder="placeholder"
        class="flex-1"
        @keyup.enter="handleAdd"
        @update:model-value="emit('update:modelValue', $event)"
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
import { Input } from '~/components/ui/input'
import { Button } from '~/components/ui/button'
import { Label } from '~/components/ui/label'
import { computed, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
}>(), {
  placeholder: 'https://example.com'
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'add': [value: string]
}>()

const errorMessage = ref('')

const isValidUrl = computed(() => {
  try {
    new URL(props.modelValue)
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
  emit('add', props.modelValue)
  emit('update:modelValue', '')
}
</script>