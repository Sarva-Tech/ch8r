<script setup lang="ts">
import type { Component } from 'vue'
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  icon?: Component | null
  title?: string
  description?: string
  class?: HTMLAttributes['class']
  containerClass?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  icon: null,
  title: 'No items found',
  description: '',
})

const emit = defineEmits<{
  action: []
}>()

function handleAction() {
  emit('action')
}
</script>

<template>
  <div :class="cn('flex flex-col items-center justify-center py-12 px-4 text-center', props.containerClass)">
    <div
      v-if="icon"
      class="flex items-center justify-center w-12 h-12 rounded-full bg-muted"
    >
      <component
        :is="icon"
        class="w-6 h-6 text-muted-foreground"
      />
    </div>
    <div class="mt-4 space-y-1">
      <h3 :class="cn('text-sm font-medium', props.class)">
        {{ title }}
      </h3>
      <p
        v-if="description"
        class="text-sm text-muted-foreground max-w-sm"
      >
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" :handle-action="handleAction" />
    </div>
  </div>
</template>
