<template>
  <div class="space-y-2">
    <Draft
      v-for="item in items"
      :key="item.id"
      :item="item"
      @remove="$emit('remove', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import Draft from './Draft.vue'
import type { DraftItem } from '~/types/knowledge-base'

defineProps<{
  items: DraftItem[]
}>()

defineEmits(['remove'])
</script>