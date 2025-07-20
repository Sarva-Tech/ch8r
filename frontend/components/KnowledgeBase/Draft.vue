<template>
  <div class="flex items-center justify-between px-2 py-1 bg-muted rounded-sm">
    <div class="flex items-center gap-3 overflow-hidden">
      <component :is="source.icon" class="w-4 h-4 text-muted-foreground shrink-0" />
      <div class="flex flex-col truncate">
        <span class="text-sm font-medium truncate">
          {{ displayValue }}
        </span>
        <span class="text-xs text-muted-foreground truncate">
          {{ fileHint }}
        </span>
      </div>
    </div>
    <Trash
      class="w-4 h-4 text-destructive hover:opacity-80 shrink-0"
      @click="$emit('remove', item.id)"
    />
  </div>
</template>

<script setup lang="ts">
import { Trash } from 'lucide-vue-next'
import { KB_SOURCES } from '~/lib/consts'

const props = defineProps<{
  item: DraftItem
}>()

defineEmits(['remove'])

const displayValue = computed(() =>
  props.item.type === 'file' ? (props.item.value as File).name : (props.item.value as string)
)

const source = computed(() => KB_SOURCES.find((s) => s.value === props.item.type))

const fileHint = computed(() => {
  const label = source.value?.label ?? ''
  const type = props.item?.value?.type
  return type ? `${label} - ${type}` : label
})
</script>
