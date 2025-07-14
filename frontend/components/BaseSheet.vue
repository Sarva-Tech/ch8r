<script setup lang="ts">
import { Sheet, SheetClose, SheetContent, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'

const props = defineProps<{
  title?: string
  submitText?: string
  cancelText?: string
  onSubmit?: () => void | Promise<void>
  loading?: boolean
}>()
</script>

<template>
  <Sheet>
    <SheetTrigger as-child>
      <slot name="trigger" />
    </SheetTrigger>

    <SheetContent>
      <SheetHeader>
        <SheetTitle class="text-left">{{ title || 'Sheet Title' }}</SheetTitle>
      </SheetHeader>

      <div class="grid gap-4 p-4">
        <slot />
      </div>

      <SheetFooter>
        <div class="flex w-full justify-between gap-2">
          <SheetClose as-child>
            <Button type="button" variant="outline">
              {{ cancelText || 'Cancel' }}
            </Button>
          </SheetClose>

          <SheetClose as-child>
            <Button type="button" :disabled="props.loading"
              @click="props.onSubmit?.()"
              >
              <template v-if="props.loading">Saving...</template>
              <template v-else>{{ props.submitText || 'Submit' }}</template>
            </Button>
          </SheetClose>
        </div>
      </SheetFooter>
    </SheetContent>
  </Sheet>
</template>
