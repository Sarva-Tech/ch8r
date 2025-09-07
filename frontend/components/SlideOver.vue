<script setup lang="ts">
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Loader2 } from "lucide-vue-next"
import { ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    submitText?: string
    cancelText?: string
    onSubmit?: () => void | Promise<void>
    loading?: boolean
    open?: boolean
    disabled?: boolean
    showSubmit?: boolean
    triggerDialog?: boolean
    dialogTitle?: string
    dialogDescription?: string
    width?: string
  }>(),
  {
    submitText: 'Save',
    cancelText: 'Cancel',
    open: undefined,
    disabled: false,
    showSubmit: true,
    triggerDialog: false,
    width: ''
  }
)

const emit = defineEmits(['update:open'])
defineExpose({
  openSlide,
  closeSlide
})

const internalOpen = ref(false)

const isControlled = computed(() => props.open !== undefined)

const sheetOpen = computed({
  get() {
    return isControlled.value ? props.open! : internalOpen.value
  },
  set(value: boolean) {
    if (isControlled.value) {
      emit('update:open', value)
    } else {
      internalOpen.value = value
    }
  },
})

function openSlide() {
  sheetOpen.value = true
}

function closeSlide() {
  sheetOpen.value = false
}

const widthClass = computed(() => {
  return props.width ? `!${props.width}` : ''
})
</script>

<template>
  <Sheet :open="sheetOpen" @update:open="val => sheetOpen = val">
    <SheetTrigger as-child>
      <slot name="trigger" />
    </SheetTrigger>

    <SheetContent
      side="right"
      :class="widthClass"
    >
      <SheetHeader class="border-b">
        <SheetTitle class="text-left">{{ title }}</SheetTitle>
      </SheetHeader>

      <div
        class="mx-4 flex flex-col h-full max-h-[calc(100vh-150px)]
         overflow-x-hidden overflow-y-auto"
      >
        <slot />
      </div>

      <SheetFooter class="border-t">
        <div class="flex w-full justify-between gap-2">
          <SheetClose as-child>
            <Button type="button" variant="outline">
              {{ cancelText }}
            </Button>
          </SheetClose>

            <Button
              v-if="showSubmit"
              type="button"
              :disabled="props.disabled || props.loading"
              @click="props.onSubmit?.()"
            >
              <template v-if="props.loading">
                <Button disabled>
                  <Loader2 class="w-4 h-4 mr-2 animate-spin" />
                </Button>
              </template>
              <template v-else>{{ submitText }}</template>
            </Button>
        </div>
      </SheetFooter>
    </SheetContent>
  </Sheet>
</template>
