<script lang="ts" setup>
import { Toaster as Sonner, type ToasterProps } from 'vue-sonner'

const props = withDefaults(defineProps<ToasterProps>(), {
  duration: 3000,
  position: 'top-right',
  richColors: true, 
  closeButton: true,
  offset: '16px',
  visibleToasts: 3,
  expand: false
})
</script>

<template>
  <Sonner
    class="sonner-toaster"
    v-bind="props"
    :style="{
      '--normal-bg': 'transparent',
      '--normal-text': 'hsl(142.1, 70.6%, 45.3%)',
      '--normal-border': 'transparent',
      '--viewport-padding': '16px',
      '--z-index': '1000'
    }"
  />
</template>
