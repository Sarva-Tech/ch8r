<template>
  <div class="mt-8 space-y-6">
    <template v-for="(items, type) in props.items" :key="type">
      <div v-if="items.length > 0" class="space-y-3">
        <ul class="space-y-2">
          <li
            v-for="item in items"
            :key="item.id"
            class="flex justify-between items-center p-3 bg-muted rounded-lg"
          >
            <div class="flex flex-col">
              <span class="text-sm font-medium">{{ item.profileName }}</span>
              <span class="text-xs text-muted-foreground">{{ item.value }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              class="text-destructive hover:text-destructive/80"
              @click="$emit('remove', item.id)"
            >
              <Trash2Icon class="h-4 w-4" />
            </Button>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Button } from '~/components/ui/button'
import { Trash2Icon } from 'lucide-vue-next'

const props = defineProps<{
  items: Record<string, Array<{
    id: string
    profileName: string
    value: string
  }>>
}>()

defineEmits(['remove'])
</script>