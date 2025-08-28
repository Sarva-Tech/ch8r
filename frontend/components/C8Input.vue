<script setup lang="ts">
import { computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'

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

const inputId = props.id || `input-${Math.random().toString(36).substring(2, 8)}`
const inputClasses = computed(() => [
  props.error
    ? 'border-destructive focus:border-destructive focus:ring-destructive'
    : 'border-input',
])

const emitDebounced = useDebounceFn((val: string) => {
  emit('update:modelValue', val)
}, 200)

const localValue = computed({
  get: () => props.modelValue,
  set: (val: string) => {
    emitDebounced(val)
  },
})
</script>

<template>
  <div class="space-y-3">
    <C8Label :for="inputId" :message="label" :required="required" />
    <Input
      :id="inputId"
      v-model="localValue"
      :type="type"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :class="inputClasses"
    />

    <p
      v-if="error"
      class="text-sm text-destructive"
    >
      {{ error }}
    </p>
  </div>
</template>
