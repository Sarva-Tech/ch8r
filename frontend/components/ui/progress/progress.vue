<script setup lang="ts">
import { ProgressRoot, ProgressIndicator } from 'reka-ui'
import { cn } from '@/lib/utils'

interface ProgressProps {
  value?: number
  max?: number
  class?: string
}

const props = withDefaults(defineProps<ProgressProps>(), {
  max: 100
})
</script>

<template>
  <ProgressRoot
    :class="cn(
      'relative h-2 w-full overflow-hidden rounded-full bg-secondary',
      props.class
    )"
    :max="props.max"
  >
    <ProgressIndicator
      :class="cn('h-full w-full flex-1 bg-primary transition-all')"
      :style="`transform: translateX(-${100 - ((props.value || 0) / props.max) * 100}%)`"
    />
  </ProgressRoot>
</template>
