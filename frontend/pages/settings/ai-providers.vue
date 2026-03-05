<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
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
            <span class="inline-flex gap-2">
              <span>Provider: {{ AIProvider.provider }}</span>
              <span>Base URL: {{ AIProvider.metadata?.base_url }}</span>
            </span>
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
import C8Item from "~/components/C8Item.vue";
import {ItemDescription} from "~/components/ui/item";
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { useAIProviderIcon } from '~/composables/useAIProviderIcon'
import { PencilLine, Trash } from 'lucide-vue-next'
const updateAIProviderSlide = ref<InstanceType<typeof UpdateAIProvider> | null>(null)
const isDeleteDialogOpen = ref(false)
const providerToDelete = ref<AIProvider | null>(null)

const AIProviderStore = useAIProviderStore()
const user = useUserStore()

const loading = ref(false)

function getAIProviderIcon(provider: string) {
  return useAIProviderIcon(provider).value
}

function canManageProvider(AIProvider: AIProvider) {
  return user.authUser?.id === AIProvider.creator
}

onMounted(async () => {
  loading.value = true
  try {
    await AIProviderStore.load()
  } catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load AI providers')
  } finally {
    loading.value = false
  }
})

const AIProviders = computed(() =>
  AIProviderStore.AIProviders.map((AIProvider) => ({
    ...AIProvider
  }))
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
