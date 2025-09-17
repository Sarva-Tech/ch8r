<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { defineProps, defineEmits, ref, onMounted } from 'vue'
import { Loader2 } from 'lucide-vue-next'

interface Props {
  label?: string
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  disabled?: boolean
  loading?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const labelWidth = ref<number | null>(null)
const labelRef = ref<HTMLElement | null>(null)

onMounted(() => {
  if (labelRef.value) {
    labelWidth.value = labelRef.value.offsetWidth
  }
})

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
    <span :style="{ width: labelWidth ? labelWidth + 'px' : 'auto' }" class="inline-flex justify-center">
      <template v-if="props.loading">
        <Loader2 class="w-4 h-4 animate-spin" />
      </template>
      <template v-else>
        <span ref="labelRef">
          <slot>{{ props.label }}</slot>
        </span>
      </template>
    </span>
  </Button>
</template>
