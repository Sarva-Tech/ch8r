<template>
  <div class="space-y-2">
    <Label for="for_text" class="text-sm font-medium">Text</Label>
    <Textarea
      :model-value="modelValue"
      :placeholder="placeholder"
      class="max-h-100 overflow-y-auto resize-none"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <div class="flex justify-end">
      <Button
        variant="secondary"
        @click="handleAdd"
        :disabled="!modelValue.trim()"
      >
        Add Text
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Textarea } from '~/components/ui/textarea'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'

const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'add': []
}>()

const handleAdd = () => {
  if (props.modelValue.trim()) {
    emit('add')
  }
}
</script>