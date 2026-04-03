<template>
  <div class="space-y-4">
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
    </div>

    <!-- Crawling Configuration -->
    <div class="space-y-3 border rounded-md p-3 bg-accent/5">
      <div class="flex items-center justify-between">
        <Label class="text-sm font-medium flex items-center gap-2">
          <Globe class="w-4 h-4" />
          Enable Web Crawling
        </Label>
        <Switch
          v-model="crawlingConfig.enable_crawling"
          :disabled="validating"
        />
      </div>

      <div v-if="crawlingConfig.enable_crawling" class="space-y-3 pl-6 border-l-2 border-muted">
        <div class="text-sm text-muted-foreground">
          Discover and extract content from linked pages on the same website
        </div>

        <!-- Fixed Configuration Display -->
        <div class="bg-muted/50 p-3 rounded-lg">
          <div class="text-sm font-medium mb-2">Crawling Configuration</div>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-muted-foreground">Max Depth:</span>
              <span class="ml-2 font-mono">{{ crawlingConfig.enable_crawling ? '1 (default)' : 'Disabled' }}</span>
            </div>
            <div>
              <span class="text-muted-foreground">Max Pages:</span>
              <span class="ml-2 font-mono">{{ crawlingConfig.enable_crawling ? '50 (default)' : 'Disabled' }}</span>
            </div>
          </div>
          <div class="text-xs text-muted-foreground mt-2">
            Configuration is optimized for balanced performance and comprehensive coverage
          </div>
        </div>

        <div class="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded">
          <AlertCircle class="w-3 h-3" />
          <span>Crawling respects robots.txt and includes rate limiting</span>
        </div>
      </div>
    </div>

    <!-- Validation Results -->
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
      <div v-if="crawlingConfig.enable_crawling" class="mt-2 pt-2 border-t text-xs text-blue-600">
        <div class="flex items-center gap-1">
          <Globe class="w-3 h-3" />
          <span>Crawling will be enabled (max depth: {{ crawlingConfig.max_depth }}, max pages: {{ crawlingConfig.max_pages }})</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useKBDraftStore } from '~/stores/kbDraft'
import { CheckCircle, Loader2, Globe, AlertCircle } from 'lucide-vue-next'
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

const crawlingConfig = ref({
  enable_crawling: false
})

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

    kbDraft.addUrl(localUrl.value, crawlingConfig.value)
    localUrl.value = ''
    validationResult.value = null

    if (crawlingConfig.value.enable_crawling) {
      toast.success('URL added with crawling enabled')
    } else {
      toast.success('URL added successfully')
    }
  } catch (error: any) {
    errorMessage.value = error.message
    toast.error(error.message)
  }
}
</script>
