<template>
  <form
    class="space-y-5"
    @submit.prevent="$emit('submit')"
  >
    <C8APIAlert :api-error="apiError" />

    <FormField
      v-if="!provider"
      v-slot="{ componentField }"
      name="provider"
    >
      <FormItem>
        <FormLabel class="flex items-center">
          Integration
          <RequiredLabel />
        </FormLabel>
        <C8Select
          :options="providerOptions"
          v-bind="componentField"
          placeholder="Select integration"
        />
        <FormMessage />
      </FormItem>
    </FormField>

    <div
      v-else
      class="flex items-center gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm"
    >
      <component
        :is="getProviderIcon(provider.id)"
        v-if="getProviderIcon(provider.id)"
        class="h-4 w-4"
      />
      <span class="font-medium">{{ provider.label }}</span>
    </div>

    <FormField
      v-slot="{ componentField }"
      name="token"
    >
      <FormItem>
        <FormLabel class="flex items-center">
          Token
          <RequiredLabel />
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            type="password"
            placeholder="Enter your token"
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
          Connection Name
          <RequiredLabel />
        </FormLabel>
        <FormControl>
          <div class="flex gap-2">
            <Input
              v-bind="componentField"
              placeholder="My Integration"
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
import C8Select from '~/components/C8Select.vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8Button from '~/components/C8Button.vue'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import { Input } from '~/components/ui/input'
import { useIntegrationStore } from '~/stores/integration'
import { useIntegrationIcon } from '~/composables/useIntegrationIcon'
import { Sparkles } from 'lucide-vue-next'
import type { FormError } from '~/composables/useApiErrorHandling'
import type { SupportedIntegration } from '~/stores/integration'

defineProps<{
  apiError: FormError | null
  provider?: SupportedIntegration
}>()

defineEmits<{
  submit: []
  'generate-name': []
}>()

const integrationStore = useIntegrationStore()

const providerOptions = computed(() =>
  integrationStore.supportedIntegrations.map(p => ({
    label: p.label,
    value: p.id,
    icon: useIntegrationIcon(p.id).value,
  })),
)

function getProviderIcon(providerId: string) {
  return useIntegrationIcon(providerId).value
}
</script>
