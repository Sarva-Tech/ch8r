<template>
  <AlertDialog :open="isOpen" @update:open="handleOpenChange">
    <AlertDialogTrigger v-if="$slots.trigger" as-child>
      <slot name="trigger" />
    </AlertDialogTrigger>
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle v-if="title">{{ title }}</AlertDialogTitle>
        <AlertDialogDescription v-if="description">
          {{ description }}
        </AlertDialogDescription>
        <slot v-else name="description" />
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel v-if="showCancel" @click="handleCancel">
          {{ cancelText }}
        </AlertDialogCancel>
        <AlertDialogAction :class="destructive ? cn(buttonVariants({ variant: 'destructive' })) : ''" @click="handleConfirm">
          {{ confirmText }}
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'
import { buttonVariants } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'

interface Props {
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
  isOpen?: boolean
  destructive?: boolean
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'confirm' | 'cancel'): void
}

withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  confirmText: 'Continue',
  cancelText: 'Cancel',
  showCancel: true,
  isOpen: false,
  destructive: false
})

const emit = defineEmits<Emits>()

const handleOpenChange = (value: boolean) => {
  emit('update:open', value)
}

const handleConfirm = () => {
  emit('confirm')
  emit('update:open', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:open', false)
}
</script>
