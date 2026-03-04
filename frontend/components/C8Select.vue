<template>
  <div :class="containerClass" class="space-y-2">
    <div v-if="label">
      <label class="text-sm font-medium">{{ label }}</label>
    </div>
    <Select v-model="internalValue" :disabled="disabled" class="w-full">
      <SelectTrigger :class="triggerClass" class="w-full">
        <SelectValue :placeholder="placeholder" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="option in options"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>

<script setup lang="ts">
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '~/components/ui/select'
import { computed } from 'vue'

const props = defineProps<{
  modelValue?: string | null
  label?: string
  placeholder?: string
  options: { label: string; value: string | number; logo?: string }[]
  disabled?: boolean
  containerClass?: string
  triggerClass?: string
}>()

const emit = defineEmits(['update:modelValue'])

const internalValue = computed({
  get: () => props.modelValue ?? null,
  set: (val) => emit('update:modelValue', val),
})</script>
