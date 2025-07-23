<template>
  <div class="space-y-2">
    <Label for="kb_source" class="text-sm font-medium">
      <slot>Knowledge Base Source</slot>
    </Label>
    <Select v-model="selectedValue">
      <SelectTrigger class="w-full">
        <div class="flex items-center gap-2 text-sm text-muted-foreground">
          <component
            :is="selectedSource.icon"
            v-if="selectedSource"
            class="w-4 h-4"
          />
          <span>
            {{ selectedSource?.label || 'Select Source' }}
          </span>
        </div>
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectItem
            v-for="source in sources"
            :key="source.value"
            :value="source.value"
          >
            <component :is="source.icon" class="w-4 h-4" />
            {{ source.label }}
          </SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  </div>
</template>

<script setup lang="ts">
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger } from '~/components/ui/select'
import { Label } from '~/components/ui/label'
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string
  sources: Array<{ value: string; label: string; icon: any }>
}>()

const emit = defineEmits(['update:modelValue'])

const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const selectedSource = computed(() =>
  props.sources.find((s) => s.value === selectedValue.value)
)
</script>