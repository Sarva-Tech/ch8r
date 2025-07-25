<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  id: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    required: true
  }
})
defineEmits(['update:modelValue'])
const inputId = computed(() => props.id || `input-${Math.random().toString(36).substring(2, 8)}`)
</script>

<template>
  <div class="space-y-2">
    <label :for="inputId" class="text-sm font-medium flex items-center gap-1">
      {{ label }}
      <span
        v-if="required"
        class="text-xs text-muted-foreground italic ml-1"
      >
        Required
      </span>
    </label>
    <input
      :id="inputId"
      :placeholder="placeholder"
      :required="required"
      class="rounded-lg border  focus:border-primary  shadow-sm text-sm px-3 py-2"
      :value="modelValue"
      @input="$emit('update:modelValue', $event?.target?.value)"
    />
  </div>
</template>
