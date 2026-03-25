<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewAIProvider />
        </div>
      </div>

      <C8Item
        v-for="(AIProvider, index) in AIProviders"
        :key="index"
        :icon="getAIProviderIcon(AIProvider.provider)"
        container-class="w-full"
        item-class="w-full"
      >
        <template #title>
          {{ AIProvider.name }}
        </template>
        <template #details>
          <ItemDescription>
            <div class="inline-flex space-x-3">
              <div
                class="flex items-center space-x-1"
              >
                <Server class="w-4 h-4" />
                <div> {{ providerDisplayName(AIProvider.provider) }} </div>
              </div>
              <div
                v-if="AIProvider.metadata?.base_url"
                class="flex items-center space-x-1"
              >
                <Globe class="w-4 h-4" />
                <div>{{ AIProvider.metadata?.base_url }} </div>
              </div>
              <div
                class="flex items-center space-x-1"
              >
                <FileBox class="w-4 h-4" />
                <div> {{ AIProvider.modelsCount }} </div>
              </div>
            </div>
          </ItemDescription>
        </template>

        <template #dropdown>
          <DropdownMenuItem
            :disabled="!canManageProvider(AIProvider)"
            @click="updateAIProvider(AIProvider)"
          >
            <PencilLine class="h-4 w-4" />
            Update
          </DropdownMenuItem>
          <DropdownMenuItem
            class="text-destructive"
            :disabled="!canManageProvider(AIProvider)"
            @click="openDeleteDialog(AIProvider)"
          >
            <Trash class="h-4 w-4 text-destructive" />
            Delete
          </DropdownMenuItem>
        </template>
      </C8Item>
      <UpdateAIProvider ref="updateAIProviderSlide" />
      <C8Dialog
        v-model:open="isDeleteDialogOpen"
        :title="`Delete AI Provider ${providerToDelete?.name}`"
        :confirm-text="'Delete'"
        :destructive="true"
        @confirm="confirmDelete"
      >
        <template #description>
          <div>
            Are you sure you want to delete the AI provider <span class="font-bold"> {{ providerToDelete?.name }} </span>?
          </div>
        </template>
      </C8Dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import NewAIProvider from '~/components/AIProvider/NewAIProvider.vue'
import UpdateAIProvider from '~/components/AIProvider/UpdateAIProvider.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import { toast } from 'vue-sonner'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { useAIProviderIcon } from '~/composables/useAIProviderIcon'
import { PencilLine, Trash, Globe, Server, FileBox } from 'lucide-vue-next'

const updateAIProviderSlide = ref<InstanceType<typeof UpdateAIProvider> | null>(null)
const isDeleteDialogOpen = ref(false)
const providerToDelete = ref<AIProvider | null>(null)

const AIProviderStore = useAIProviderStore()
const AIProviderModelsStore = useAIProviderModelsStore()
const user = useUserStore()

const loading = ref(false)

function getAIProviderIcon(provider: string) {
  return useAIProviderIcon(provider).value
}

function canManageProvider(AIProvider: AIProvider) {
  return user.authUser?.id === AIProvider.creator
}

function providerDisplayName(provider: string) {
  switch (provider.toLowerCase()) {
    case 'gemini':
      return 'Gemini'
    case 'custom':
      return 'Custom'
    case 'openai':
      return 'OpenAI'
    case 'anthropic':
      return 'Anthropic'
    case 'cohere':
      return 'Cohere'
    default:
      return provider.charAt(0).toUpperCase() + provider.slice(1)
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await AIProviderStore.load()
    await AIProviderModelsStore.load()
  }
  catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load AI providers')
  }
  finally {
    loading.value = false
  }
})

const AIProviders = computed(() =>
  AIProviderStore.AIProviders.map((AIProvider) => {
    const providerModelData = AIProviderModelsStore.providerModels.find(
      pm => pm.ai_provider.uuid === AIProvider.uuid,
    )
    return {
      ...AIProvider,
      models: providerModelData?.ai_provider_models?.models_data || [],
      modelsCount: providerModelData?.ai_provider_models?.models_data?.length || 0,
    }
  }),
)

function updateAIProvider(AIProvider: AIProvider) {
  updateAIProviderSlide.value?.open(AIProvider)
}

function openDeleteDialog(AIProvider: AIProvider) {
  providerToDelete.value = AIProvider
  isDeleteDialogOpen.value = true
}

function confirmDelete() {
  if (providerToDelete.value) {
    deleteAIProvider(providerToDelete.value)
  }
}

function deleteAIProvider(AIProvider: AIProvider) {
  AIProviderStore.delete(AIProvider.uuid).then((response) => {
    if (response?.detail === 'deleted') {
      toast.success('AI provider deleted')
    }
  })
}
</script>
