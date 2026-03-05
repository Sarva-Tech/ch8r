<template>
  <Alert v-if="apiError && apiError.error" variant="destructive">
    <AlertCircleIcon />
    <AlertTitle>{{ apiError.error }}</AlertTitle>
    <AlertDescription v-if="apiError.details">
      <p> {{ apiError.details }} </p>
    </AlertDescription>
  </Alert>
</template>

<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { AlertCircleIcon } from 'lucide-vue-next'

interface APIError {
  error?: string
  details?: string
}

defineProps<{
  apiError: APIError | null
}>()
</script>
