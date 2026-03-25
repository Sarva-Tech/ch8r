<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { defineProps, defineEmits } from 'vue'
import type { Component } from 'vue'
import { Loader2 } from 'lucide-vue-next'

interface Props {
  label?: string
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  disabled?: boolean
  loading?: boolean
  icon?: Component
  iconPosition?: 'left' | 'right'
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<template>
  <Button
    :variant="props.variant || 'default'"
    :size="props.size || 'default'"
    :disabled="props.disabled || props.loading"
    class="flex justify-center items-center"
    @click="handleClick"
  >
    <span class="inline-flex justify-center">
      <template v-if="props.loading">
        <Loader2 class="w-4 h-4 animate-spin" />
      </template>
      <template v-else>
        <span class="inline-flex items-center gap-2">
          <component
            :is="props.icon"
            v-if="props.icon && (!props.iconPosition || props.iconPosition === 'left')"
            class="w-4 h-4"
          />
          <slot
            v-else-if="!props.icon && (!props.iconPosition || props.iconPosition === 'left')"
            name="icon-left"
          />
          <slot>{{ props.label }}</slot>

          <component
            :is="props.icon"
            v-if="props.icon && props.iconPosition === 'right'"
            class="w-4 h-4"
          />
          <slot
            v-else-if="!props.icon"
            name="icon-right"
          />
        </span>
      </template>
    </span>
  </Button>
</template>
