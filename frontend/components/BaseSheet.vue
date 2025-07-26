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
import { ref, computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    submitText?: string
    cancelText?: string
    onSubmit?: () => void | Promise<void>
    loading?: boolean
    open?: boolean
  }>(),
  {
    submitText: 'Save',
    cancelText: 'Cancel',
    open: undefined,
  }
)

const emit = defineEmits(['update:open'])

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
</script>

<template>
  <Sheet :open="sheetOpen" @update:open="val => sheetOpen = val">
    <SheetTrigger as-child>
      <slot name="trigger" />
    </SheetTrigger>

    <SheetContent>
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

          <SheetClose as-child>
            <Button
              type="button"
              :disabled="props.loading"
              @click="props.onSubmit?.()"
            >
              <template v-if="props.loading">Saving...</template>
              <template v-else>{{ submitText }}</template>
            </Button>
          </SheetClose>
        </div>
      </SheetFooter>
    </SheetContent>
  </Sheet>
</template>
