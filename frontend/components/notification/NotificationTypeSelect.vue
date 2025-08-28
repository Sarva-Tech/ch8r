<template>
  <div class="space-y-2">
    <div>
      <label class="text-sm font-medium">Select Notification Type</label>
    </div>
    <Select v-model="modelValue" class="w-full">
      <SelectTrigger class="w-full">
        <SelectValue placeholder="Choose type..." />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="discord">Discord</SelectItem>
        <SelectItem value="slack">Slack</SelectItem>
        <SelectItem value="email">Email</SelectItem>
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

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits(['update:modelValue'])

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})
</script>
