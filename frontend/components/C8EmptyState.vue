<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  icon?: Component
  title?: string
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Nothing here yet',
  description: 'Get started by creating your first one.',
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-20 px-6 text-center">
    <div class="mb-5 flex items-center justify-center w-16 h-16 rounded-2xl bg-muted border border-border">
      <component
        :is="props.icon"
        v-if="props.icon"
        class="w-8 h-8 text-muted-foreground"
      />
      <slot v-else name="icon" />
    </div>
    <p class="text-base font-semibold text-foreground mb-1">{{ props.title }}</p>
    <p class="text-sm text-muted-foreground max-w-xs">{{ props.description }}</p>
    <div v-if="$slots.action" class="mt-6">
      <slot name="action" />
    </div>
  </div>
</template>
