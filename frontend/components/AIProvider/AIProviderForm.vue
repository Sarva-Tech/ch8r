<template>
  <form
    class="space-y-5"
    @submit.prevent="$emit('submit')"
  >
    <C8APIAlert :api-error="apiError" />

    <FormField
      v-slot="{ componentField }"
      name="provider"
    >
      <FormItem>
        <FormLabel class="flex items-center">
          AI Provider
          <RequiredLabel />
        </FormLabel>
        <C8Select
          :options="providerOptions"
          v-bind="componentField"
        />
      </FormItem>
    </FormField>

    <FormField
      v-if="shouldShowBaseUrl"
      v-slot="{ componentField }"
      name="base_url"
    >
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            Base URL
            <RequiredLabel v-if="isCustomProvider" />
          </div>
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            placeholder="https://api.openai.com/v1"
            :disabled="!isCustomProvider"
          />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>

    <FormField
      v-slot="{ componentField }"
      name="provider_api_key"
    >
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            API Key
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            type="password"
            placeholder="org-YvnH2WW0YjzHn0gAUzh7JY3q"
          />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>

    <FormField
      v-slot="{ componentField }"
      name="name"
    >
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            Connection Name
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <div class="flex gap-2">
            <Input
              v-bind="componentField"
              placeholder="Ch8r Dev"
              class="flex-1"
            />
            <C8Button
              variant="outline"
              size="icon"
              type="button"
              @click="$emit('generate-name')"
            >
              <Sparkles class="h-4 w-4" />
            </C8Button>
          </div>
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>
  </form>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFormValues } from 'vee-validate'
import C8Select from '~/components/C8Select.vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8Button from '~/components/C8Button.vue'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import { Input } from '~/components/ui/input'
import { useAIProviderIcon } from '~/composables/useAIProviderIcon'
import { Sparkles } from 'lucide-vue-next'
import type { FormError } from '~/composables/useApiErrorHandling'

defineProps<{
  apiError: FormError | null
}>()

defineEmits<{
  submit: []
  'generate-name': []
}>()

const AIProviderStore = useAIProviderStore()
const values = useFormValues()

const providerOptions = computed(() =>
  AIProviderStore.supportedAIProviders.map(p => ({
    label: p.label,
    value: p.id,
    baseUrl: p.base_url,
    icon: useAIProviderIcon(p.id).value,
  })),
)

const isCustomProvider = computed(() => values.value.provider === 'custom')
const shouldShowBaseUrl = computed(() => isCustomProvider.value || values.value.provider === '')
</script>
