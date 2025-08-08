<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: string
  label?: string
  id?: string
  required?: boolean
  placeholder: string
  error?: string
  type?: 'text' | 'email' | 'password' | 'url' | 'number'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: '',
  id: '',
  required: false,
  type: 'text',
  disabled: false,
  error: ''
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputId = computed(() => props.id || `input-${Math.random().toString(36).substring(2, 8)}`)
const inputClasses = computed(() => [
  'w-full rounded-lg border shadow-sm text-sm px-3 py-2 transition-colors',
  'focus:border-primary focus:ring-1 focus:ring-primary',
  props.error
    ? 'border-destructive focus:border-destructive focus:ring-destructive'
    : 'border-input',
  props.disabled ? 'bg-muted cursor-not-allowed opacity-50' : 'bg-background'
])
</script>

<template>
  <div class="space-y-2">
    <label
      v-if="label"
      :for="inputId"
      class="text-sm font-medium flex items-center gap-1"
    >
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
      :type="type"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :class="inputClasses"
      :value="modelValue"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    >

    <p
      v-if="error"
      class="text-sm text-destructive"
    >
      {{ error }}
    </p>
  </div>
</template>