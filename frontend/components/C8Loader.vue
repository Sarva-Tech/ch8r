<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { LoaderIcon } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
  containerClass?: HTMLAttributes['class']
}>()
</script>

<template>
  <div :class="cn('flex', props.containerClass)">
    <LoaderIcon
      role="status"
      aria-label="Loading"
      :class="cn('size-4 animate-spin', props.class)"
    />
  </div>
</template>
