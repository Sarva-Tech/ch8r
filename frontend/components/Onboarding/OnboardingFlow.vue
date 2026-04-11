<template>
  <div
    class="flex flex-col items-center justify-center w-full px-6 py-12 max-w-4xl mx-auto gap-8 min-h-full"
  >
    <span
      v-if="currentStep <= 2"
      class="text-xs font-medium text-muted-foreground bg-muted px-3 py-1 rounded-full"
    >
      Step {{ currentStep }} of 2
    </span>

    <div
      v-if="currentStep === 1"
      class="w-full max-w-lg space-y-4"
    >
      <div class="space-y-1">
        <h2 class="text-xl font-semibold">
          Connect an AI Provider
        </h2>
        <p class="text-sm text-muted-foreground">
          To start chatting, you'll need to connect at least one AI provider. This lets the app communicate with AI services on your behalf.
        </p>
      </div>
      <NewAIProvider :inline="true" />
    </div>

    <div
      v-else-if="currentStep === 2"
      class="w-full max-w-lg space-y-4"
    >
      <div class="space-y-1">
        <h2 class="text-xl font-semibold">
          Configure a Text Model
        </h2>
        <p class="text-sm text-muted-foreground">
          Now select the AI model that will generate responses in this chatroom.
        </p>
      </div>
      <ConfigureAIModels :config="textModelConfig" />
    </div>

    <div
      v-else-if="hasOptionalCards"
      class="w-full space-y-6"
    >
      <div class="space-y-1 text-center">
        <h2 class="text-xl font-semibold">
          Take the most out of ch8r
        </h2>
        <p class="text-sm text-muted-foreground">
          You're all set to chat. Here are a few more things you can configure.
        </p>
      </div>

      <div class="flex flex-wrap justify-center gap-4 w-full">
        <NuxtLink
          v-if="!hasAppIntegration"
          to="/settings/integrations"
          class="group rounded-lg border bg-card p-5 space-y-2 hover:border-primary hover:shadow-sm transition-all cursor-pointer w-72"
        >
          <div class="flex items-center gap-2">
            <Plug class="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            <h3 class="font-medium text-sm">
              Connect Integrations
            </h3>
          </div>
          <p class="text-xs text-muted-foreground">
            Link third-party services like GitHub to enable tools and automation in your application.
          </p>
          <span class="text-xs text-primary flex items-center gap-1">
            Go to Settings <ArrowRight class="w-3 h-3" />
          </span>
        </NuxtLink>

        <NuxtLink
          v-if="!hasAppIntegration"
          :to="`/applications/${appUuid}/settings?tab=integrations`"
          class="group rounded-lg border bg-card p-5 space-y-2 hover:border-primary hover:shadow-sm transition-all cursor-pointer w-72"
        >
          <div class="flex items-center gap-2">
            <Settings class="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            <h3 class="font-medium text-sm">
              Configure App Integration
            </h3>
          </div>
          <p class="text-xs text-muted-foreground">
            Connect an integration to this specific app so the AI can use its tools.
          </p>
          <span class="text-xs text-primary flex items-center gap-1">
            Go to App Settings <ArrowRight class="w-3 h-3" />
          </span>
        </NuxtLink>

        <NuxtLink
          v-if="!hasKnowledgeBase"
          :to="`/applications/${appUuid}/knowledge-base`"
          class="group rounded-lg border bg-card p-5 space-y-2 hover:border-primary hover:shadow-sm transition-all cursor-pointer w-72"
        >
          <div class="flex items-center gap-2">
            <BookOpen class="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            <h3 class="font-medium text-sm">
              Add a Knowledge Base
            </h3>
          </div>
          <p class="text-xs text-muted-foreground">
            Upload files, URLs, or text so the AI can reference your content when responding.
          </p>
          <span class="text-xs text-primary flex items-center gap-1">
            Go to Knowledge Base <ArrowRight class="w-3 h-3" />
          </span>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Plug, Settings, BookOpen, ArrowRight } from 'lucide-vue-next'
import NewAIProvider from '~/components/AIProvider/NewAIProvider.vue'
import ConfigureAIModels from '~/components/App/ConfigureAIModels.vue'
import { useAppIntegrationStore } from '~/stores/appIntegration'

const AIProviderStore = useAIProviderStore()
const AppAIProviderStore = useAppAIProviderStore()
const appStore = useApplicationsStore()
const appIntegrationStore = useAppIntegrationStore()
const kbStore = useKnowledgeBaseStore()

const appUuid = computed(() => appStore.selectedApplication?.uuid ?? '')

const hasAIProvider = computed(() => AIProviderStore.AIProviders.length > 0)
const hasTextModel = computed(() =>
  AppAIProviderStore.existingAppAIProviderConfigs.some(
    c => c.capability === 'text' && c.context === 'response',
  ),
)
const hasAppIntegration = computed(() => appIntegrationStore.appIntegrations.length > 0)
const hasKnowledgeBase = computed(() => kbStore.kbs.length > 0)
const hasOptionalCards = computed(() => !hasAppIntegration.value || !hasKnowledgeBase.value)

const currentStep = computed(() => {
  if (!hasAIProvider.value) return 1
  if (!hasTextModel.value) return 2
  return 3
})

onMounted(async () => {
  if (appUuid.value) {
    await Promise.allSettled([
      appIntegrationStore.load(appUuid.value),
      kbStore.load(),
    ])
  }
})

const textModelConfig = {
  title: 'Text Generation Model',
  description: 'Select the model that will generate AI responses in this application.',
  modelLabel: 'Model',
  modelPlaceholder: 'Select a model',
  capability: 'text',
  context: 'response',
  successMessage: 'Text model configured',
}
</script>
