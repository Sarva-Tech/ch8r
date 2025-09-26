<script setup lang="ts">
import { ref, computed } from "vue"
import { useFilter } from "reka-ui"
import {
  Combobox,
  ComboboxAnchor,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxList
} from "@/components/ui/combobox"

// Props
const props = defineProps({
  options: {
    type: Array as PropType<{ value: string; label: string }[]>,
    required: true
  },
  placeholder: {
    type: String,
    default: "Select..."
  },
  label: {
    type: String,
    default: ""
  }
})

const modelValue = defineModel<string[]>({ default: [] })

const open = ref(false)
const searchTerm = ref("")

const { contains } = useFilter({ sensitivity: "base" })

const filteredOptions = computed(() => {
  const options = props.options.filter(i => !modelValue.value.includes(i.value))
  return searchTerm.value
    ? options.filter(option => contains(option.label, searchTerm.value))
    : options
})

function handleSelect(option: { value: string; label: string }) {
  if (!modelValue.value.includes(option.value)) {
    modelValue.value = [...modelValue.value, option.value]
  }
  searchTerm.value = ""
  if (filteredOptions.value.length === 0) {
    open.value = false
  }
}
</script>

<template>
  <Combobox v-model="modelValue" v-model:open="open" :ignore-filter="true">
    <ComboboxAnchor as-child>
      <TagsInput v-model="modelValue" class="px-2 gap-2 w-full">
        <div class="flex gap-2 flex-wrap items-center">
          <TagsInputItem v-for="item in modelValue" :key="item" :value="item">
            <TagsInputItemText />
            <TagsInputItemDelete />
          </TagsInputItem>
        </div>

        <ComboboxInput v-model="searchTerm" as-child>
          <TagsInputInput
            :placeholder="placeholder"
            class="min-w-[200px] w-full p-0 border-none focus-visible:ring-0 h-auto"
            @keydown.enter.prevent
          />
        </ComboboxInput>
      </TagsInput>

      <ComboboxList class="w-[--reka-popper-anchor-width]">
        <ComboboxEmpty>No options available</ComboboxEmpty>
        <ComboboxGroup>
          <ComboboxItem
            v-for="option in filteredOptions"
            :key="option.value"
            :value="option.value"
            @select.prevent="handleSelect(option)"
          >
            {{ option.label }}
          </ComboboxItem>
        </ComboboxGroup>
      </ComboboxList>
    </ComboboxAnchor>
  </Combobox>
</template>
