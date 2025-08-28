<script lang="ts" setup>
import { cn } from "@/lib/utils"
import { Label } from '@/components/ui/label'

const props = defineProps({
  required: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    required: true
  },
  class: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <Label
    data-slot="form-label"
    :class="cn(
      'data-[error=true]:text-destructive-foreground',
      props.class,
    )"
  >
    {{ message }}
    <span
      v-if="required"
      class="text-xs text-muted-foreground italic ml-1"
    >
      Required
    </span>
  </Label>
</template>
