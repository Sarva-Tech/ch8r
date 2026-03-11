<script setup lang="ts">
import { ref, computed } from 'vue'
import { useFilter } from 'reka-ui'
import { ChevronsUpDownIcon, XIcon } from 'lucide-vue-next'
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

const props = defineProps({
  options: {
    type: Array as PropType<{ value: string, label: string }[]>,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Select or add items',
  },
  label: {
    type: String,
    default: '',
  },
  allowCustomValues: {
    type: Boolean,
    default: true,
  },
  multiple: {
    type: Boolean,
    default: true,
  },
  searchPlaceholder: {
    type: String,
    default: 'Type to search or add',
  },
  allSelectedMessage: {
    type: String,
    default: 'All items selected',
  },
  noResultsMessage: {
    type: String,
    default: 'No matching items',
  },
  noOptionsMessage: {
    type: String,
    default: 'No items yet. Type to add one',
  },
  addCustomHint: {
    type: String,
    default: 'Press Enter to add',
  },
})

const modelValue = defineModel<string[]>({ default: [] })

const internalValue = computed({
  get: () => {
    if (props.multiple) {
      return modelValue.value
    } else {
      return modelValue.value.length > 0 ? modelValue.value[0] : null
    }
  },
  set: (value: string[] | string | null) => {
    if (props.multiple) {
      modelValue.value = Array.isArray(value) ? value : []
    } else {
      modelValue.value = value ? [value as string] : []
    }
  }
})

const selectedValue = computed(() => props.multiple ? internalValue.value : (internalValue.value as string | null))

const emit = defineEmits<{
  'custom-value-added': [value: string]
  'item-selected': [value: string]
}>()

const open = ref(false)
const searchTerm = ref('')

const { contains } = useFilter({ sensitivity: 'base' })

const filteredOptions = computed(() => {
  const options = props.multiple
    ? props.options.filter(i => !modelValue.value.includes(i.value))
    : props.options
  return searchTerm.value
    ? options.filter(option => contains(option.label, searchTerm.value))
    : options
})

function handleSelect(option: { value: string, label: string }) {
  if (props.multiple) {
    if (!modelValue.value.includes(option.value)) {
      modelValue.value = [...modelValue.value, option.value]
      emit('item-selected', option.value)
    }
  } else {
    modelValue.value = [option.value]
    emit('item-selected', option.value)
    open.value = false
  }
  searchTerm.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && searchTerm.value.trim()) {
    event.preventDefault()
    const trimmedValue = searchTerm.value.trim()

    if (props.multiple && modelValue.value.includes(trimmedValue)) {
      return
    }

    const existingOption = props.options.find(opt =>
      opt.value === trimmedValue || opt.label === trimmedValue,
    )

    if (existingOption) {
      handleSelect(existingOption)
    }
    else if (props.allowCustomValues) {
      if (props.multiple) {
        modelValue.value = [...modelValue.value, trimmedValue]
        emit('custom-value-added', trimmedValue)
        emit('item-selected', trimmedValue)
      } else {
        modelValue.value = [trimmedValue]
        emit('custom-value-added', trimmedValue)
        emit('item-selected', trimmedValue)
        open.value = false
      }
      searchTerm.value = ''
    }
  }
}

function removeTag(value: string) {
  modelValue.value = modelValue.value.filter(item => item !== value)
}

function getDisplayLabel(value: string) {
  const option = props.options.find(opt => opt.value === value)
  return option ? option.label : value
}
</script>

<template>
  <div class="w-full">
    <Popover v-model:open="open">
      <PopoverTrigger as-child>
        <Button
          variant="outline"
          role="combobox"
          :aria-expanded="open"
          class="w-full justify-between h-9"
        >
          <span
            v-if="props.multiple ? modelValue.length > 0 : selectedValue"
            class="text-foreground truncate flex-1 text-left"
          >
            <template v-if="props.multiple">
              {{ modelValue.length }} item{{ modelValue.length === 1 ? '' : 's' }} selected
            </template>
            <template v-else>
              {{ getDisplayLabel(selectedValue as string) }}
            </template>
          </span>
          <span
            v-else
            class="text-muted-foreground truncate flex-1 text-left"
          >
            {{ placeholder }}
          </span>
          <ChevronsUpDownIcon class="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent class="p-0">
        <Command>
          <CommandInput
            v-model="searchTerm"
            :placeholder="searchPlaceholder"
            class="w-full"
            @keydown="handleKeydown"
          />
          <CommandList>
            <template v-if="filteredOptions.length === 0">
              <div class="p-2 text-sm text-muted-foreground">
                <template v-if="searchTerm">
                  <div>{{ noResultsMessage }}</div>
                  <div
                    v-if="allowCustomValues"
                    class="text-muted-foreground mt-1"
                  >
                    {{ addCustomHint }} "{{ searchTerm }}"
                  </div>
                </template>
                <template v-else-if="options.length > 0">
                  {{ allSelectedMessage }}
                </template>
                <template v-else>
                  {{ noOptionsMessage }}
                </template>
              </div>
            </template>
            <template v-else>
              <CommandGroup>
                <CommandItem
                  v-for="option in filteredOptions"
                  :key="option.value"
                  :value="option.value"
                  @select="handleSelect(option)"
                >
                  {{ option.label }}
                </CommandItem>
              </CommandGroup>
            </template>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>

    <div
      v-if="props.multiple && modelValue.length > 0"
      class="flex flex-wrap gap-2 mt-2"
    >
      <Badge
        v-for="item in modelValue"
        :key="item"
        variant="secondary"
        class="h-6 px-2 py-1 text-xs flex items-center gap-1 cursor-pointer hover:bg-secondary/80"
        @click="removeTag(item)"
      >
        {{ getDisplayLabel(item) }}
        <XIcon
          class="h-3 w-3 hover:text-destructive"
          @click.stop="removeTag(item)"
        />
      </Badge>
    </div>
  </div>
</template>
