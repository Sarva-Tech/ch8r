<script setup lang="ts">
import { useClipboard } from '@vueuse/core'
import { Copy, Check } from 'lucide-vue-next'

const props = defineProps<{
  text: string
}>()

const { copy, copied, isSupported } = useClipboard()
const handleCopy = () => {
  copy(props.text)
}
</script>

<template>
  <div v-if="isSupported">
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger as-child>
          <span
            class="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground transition-colors hover:text-foreground hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring"
            @click="handleCopy"
          >
            <transition
              enter-active-class="transform duration-200 ease-out"
              enter-from-class="scale-75 opacity-0"
              enter-to-class="scale-100 opacity-100"
              leave-active-class="transform duration-150 ease-in"
              leave-from-class="scale-100 opacity-100"
              leave-to-class="scale-75 opacity-0"
              mode="out-in"
            >
              <Check v-if="copied" key="check" class="size-4 text-green-500" />
              <Copy v-else key="copy" class="size-4" />
            </transition>
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <span>{{ copied ? 'Copied!' : 'Copy' }}</span>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  </div>
  <div v-else>
    <span class="text-sm text-muted-foreground">Clipboard not supported</span>
  </div>
</template>
