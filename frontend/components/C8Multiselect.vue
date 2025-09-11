<template>
  <div class="space-y-3">
    <Label v-if="label" class="typo__label">{{ label }}</Label>
    <multiselect
      :model-value="internalValue"
      :options="options"
      :multiple="multiple"
      :close-on-select="!multiple"
      :clear-on-select="false"
      :preserve-search="true"
      :placeholder="placeholder"
      label="label"
      track-by="value"
      :preselect-first="preselectFirst"
      :custom-label="optionLabel"
      @update:model-value="onInput"
    >
      <template #selection="{ values, isOpen }">
        <span
          v-if="values.length"
          v-show="!isOpen"
          class="multiselect__single"
        >
          {{ multiple ? values.length + ' selected' : values[0]?.label }}
        </span>
      </template>

      <template #option="{ option }">
        <span class="flex items-center gap-2">
          <component v-if="option.icon" :is="option.icon" class="w-4 h-4" />
          <span>{{ option.label }}</span>
        </span>
      </template>
    </multiselect>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, watch } from 'vue'
import Multiselect from 'vue-multiselect'
import type { SelectOption } from '~/lib/types'

const props = defineProps<{
  modelValue: SelectOption[],
  options: SelectOption[],
  multiple: boolean
  placeholder?: string
  label: string
  preselectFirst: boolean
}>()

const emit = defineEmits(['update:modelValue'])

const internalValue = ref(props.modelValue)

watch(
  () => props.modelValue,
  (newVal) => {
    internalValue.value = newVal
  }, { immediate: true }
)

const onInput = (val: SelectOption[]) => {
  internalValue.value = val
  emit('update:modelValue', val)
}

const optionLabel = (option: SelectOption) => option.label
</script>

<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
