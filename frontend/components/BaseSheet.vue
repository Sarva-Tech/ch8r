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

const props = withDefaults(
  defineProps<{
    title: string
    submitText?: string
    cancelText?: string
    onSubmit?: () => void | Promise<void>
    loading?: boolean
  }>(),
  {
    submitText: 'Save',
    cancelText: 'Cancel',
  }
)
</script>

<template>
  <Sheet>
    <SheetTrigger as-child>
      <slot name="trigger" />
    </SheetTrigger>

    <SheetContent>
      <SheetHeader>
        <SheetTitle class="text-left">{{ title }}</SheetTitle>
      </SheetHeader>

      <div class="grid gap-4 p-4">
        <slot />
      </div>

      <SheetFooter>
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
