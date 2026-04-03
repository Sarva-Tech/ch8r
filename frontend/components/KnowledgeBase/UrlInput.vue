<template>
  <div class="space-y-2">
    <Label for="url_input" class="text-sm font-medium">
      <slot>URL</slot>
    </Label>
    <div class="flex gap-2">
      <Input
        v-model="localUrl"
        :placeholder="placeholder"
        class="flex-1"
        @keyup.enter="handleAdd"
        :disabled="validating"
      />
      <Button
        variant="secondary"
        :disabled="!isValidUrl || validating"
        @click="handleAdd"
      >
        <Loader2 v-if="validating" class="w-4 h-4 animate-spin" />
        <slot name="button-text">Add URL</slot>
      </Button>
    </div>
    <p v-if="errorMessage" class="text-sm text-destructive">
      {{ errorMessage }}
    </p>
    <div v-if="validationResult && !errorMessage" class="text-sm text-muted-foreground border rounded-md p-2 bg-accent/10">
      <div class="flex items-center gap-2 mb-1">
        <CheckCircle class="w-4 h-4 text-green-500" />
        <span class="font-medium">URL validated successfully</span>
      </div>
      <div v-if="validationResult.message" class="text-xs text-yellow-600 mb-2">
        {{ validationResult.message }}
      </div>
      <div v-if="validationResult.title" class="mb-1">
        <strong>Title:</strong> {{ validationResult.title }}
      </div>
      <div v-if="validationResult.description" class="mb-1">
        <strong>Description:</strong> {{ validationResult.description }}
      </div>
      <div class="text-xs">
        <strong>Content length:</strong> {{ validationResult.content_length?.toLocaleString() || 0 }} characters
        <span v-if="validationResult.content_type">• {{ validationResult.content_type }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useKBDraftStore } from '~/stores/kbDraft'
import { CheckCircle, Loader2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

const props = withDefaults(defineProps<{
  placeholder?: string
  applicationUuid?: string
}>(), {
  placeholder: 'https://example.com'
})

const localUrl = ref('')
const errorMessage = ref('')
const validating = ref(false)
const validationResult = ref<any>(null)
const kbDraft = useKBDraftStore()

const isValidUrl = computed(() => {
  try {
    new URL(localUrl.value)
    return localUrl.value.trim() !== ''
  } catch {
    return false
  }
})

async function validateUrl(url: string) {
  if (!props.applicationUuid) {
    return null
  }

  validating.value = true
  try {
    const simpleResponse = await $fetch(`/api/applications/${props.applicationUuid}/knowledge-bases/validate_url/`, {
      method: 'POST',
      body: { url, simple_validation: true }
    })

    if (simpleResponse.valid) {
      return simpleResponse
    } else {
      throw new Error(simpleResponse.error || 'URL validation failed')
    }
  } catch (simpleError: any) {
    if (simpleError.data?.error?.includes('Invalid URL format')) {
      throw new Error(simpleError.data?.error || 'Invalid URL format')
    }

    try {
      const fullResponse = await $fetch(`/api/applications/${props.applicationUuid}/knowledge-bases/validate_url/`, {
        method: 'POST',
        body: { url, simple_validation: false }
      })

      if (fullResponse.valid) {
        return fullResponse
      } else {
        return {
          valid: true,
          title: null,
          description: null,
          content_length: 0,
          content_type: null,
          message: `URL format is valid, but content preview failed: ${fullResponse.error}. Content will be extracted during processing.`
        }
      }
    } catch (fullError: any) {
      throw new Error(`URL format is valid, but content preview failed: ${fullError.data?.error || fullError.message}. The URL will still be processed.`)
    }
  } finally {
    validating.value = false
  }
}

async function handleAdd() {
  if (!isValidUrl.value) {
    errorMessage.value = 'Please enter a valid URL (e.g., https://example.com)'
    return
  }

  errorMessage.value = ''
  validationResult.value = null

  try {
    const validation = await validateUrl(localUrl.value)
    if (validation) {
      validationResult.value = validation
      await new Promise(resolve => setTimeout(resolve, 1000))
    }

    kbDraft.addUrl(localUrl.value)
    localUrl.value = ''
    validationResult.value = null
  } catch (error: any) {
    errorMessage.value = error.message
    toast.error(error.message)
  }
}
</script>
