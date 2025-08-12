<script setup lang="ts">
import { Check, ChevronsUpDown } from "lucide-vue-next"
import { ref } from "vue"
import { Button } from "@/components/ui/button"
import {
  Combobox,
  ComboboxAnchor,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxItem,
  ComboboxItemIndicator,
  ComboboxList,
  ComboboxTrigger,
} from "@/components/ui/combobox"

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  options: {
    type: Array as PropType<{ value: string; label: string }[]>,
    required: true
  }
})

const selectedValues = ref<typeof props.options[]>([])
</script>

<template>
  <Combobox v-model="selectedValues" multiple by="label">
    <ComboboxAnchor as-child>
      <ComboboxTrigger as-child>
        <Button variant="outline" class="justify-between">
          {{ selectedValues.map(s => s.label) }}
          <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </ComboboxTrigger>
    </ComboboxAnchor>

    <ComboboxList>
      <ComboboxEmpty>
        No framework found.
      </ComboboxEmpty>

      <ComboboxGroup>
        <ComboboxItem
          v-for="option in props.options"
          :key="option.value"
          :value="option"
        >
          {{ option.label }}

          <ComboboxItemIndicator>
            <Check />
          </ComboboxItemIndicator>
        </ComboboxItem>
      </ComboboxGroup>
    </ComboboxList>
  </Combobox>
</template>
