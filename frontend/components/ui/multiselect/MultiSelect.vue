<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" size="sm" class="flex items-center">
        <span>{{ label }}</span>
        <ChevronDown class="ml-2 w-4 h-4" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" class="max-h-60 overflow-y-auto">
      <div class="p-2">
        <div v-for="option in options" :key="option.value" class="flex items-center space-x-2">
          <Checkbox
            :checked="selectedValues.includes(option.value)"
            @update:checked="handleCheckboxChange(option.value, $event)"
            class="h-4 w-4"
          />
          <span>{{ option.label }}</span>
        </div>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import { ref, defineProps, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent } from '@/components/ui/dropdown-menu'
import { ChevronDown } from 'lucide-vue-next'
import { Checkbox } from '@/components/ui/checkbox'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  options: {
    type: Array as PropType<{ value: string; label: string }[]>,
    required: true
  },
  modelValue: {
    type: Array as PropType<string[]>,
    required: true
  }
})

const selectedValues = ref<string[]>([...props.modelValue])

watch(selectedValues, (newSelectedValues) => {
  emit('update:modelValue', newSelectedValues)
})

const handleCheckboxChange = (value: string, checked: boolean) => {
  if (checked) {
    if (!selectedValues.value.includes(value)) {
      selectedValues.value.push(value)
    }
  } else {
    selectedValues.value = selectedValues.value.filter(item => item !== value)
  }
}
</script>

<style scoped>
</style>
