<template>
  <div :class="containerClass || 'space-y-2'">
    <div v-if="label">
      <label class="text-sm font-medium">{{ label }}</label>
    </div>
    <Select v-model="internalValue" :disabled="disabled" class="w-full">
      <SelectTrigger :class="triggerClass" class="w-full">
        <SelectValue :placeholder="placeholder">
          <div v-if="selectedOption" class="flex items-center gap-2">
            <component
              :is="selectedOption.icon"
              v-if="selectedOption.icon"
              class="h-4 w-4 flex-shrink-0"
            />
            <span>{{ selectedOption.label }}</span>
          </div>
          <span v-else>{{ placeholder }}</span>
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="option in options"
          :key="option.value"
          :value="option.value"
        >
          <div class="flex items-center gap-2">
            <component
              :is="option.icon" 
              v-if="option.icon"
              class="h-4 w-4 flex-shrink-0"
            />
            <span>{{ option.label }}</span>
          </div>
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
import { computed, type Component } from 'vue'

const props = defineProps<{
  modelValue?: string | null
  label?: string
  placeholder?: string
  options: { label: string; value: string | number; logo?: string; icon?: Component }[]
  disabled?: boolean
  containerClass?: string
  triggerClass?: string
}>()

const emit = defineEmits(['update:modelValue'])

const internalValue = computed({
  get: () => props.modelValue ?? null,
  set: (val) => emit('update:modelValue', val),
})

const selectedOption = computed(() => {
  return props.options.find(option => option.value === props.modelValue)
})
</script>
