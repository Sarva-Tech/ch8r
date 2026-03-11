<template>
  <div class="flex flex-col">
    <div
      class="overflow-y-auto pt-[72px] pb-[120px] px-6 space-y-6"
      :style="`height: calc(100vh - 64px - 112px);`"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        :class="
          cn(
            'flex w-fit max-w-[75%] lg:max-w-[60%] xl:max-w-[50%] flex-col gap-2 rounded-lg p-2 text-sm',
            isMessageSentByCurrentUser(message.sender_identifier)
              ? 'ml-auto bg-primary text-primary-foreground'
              : 'bg-muted',
          )
        "
      >
        <div v-html="md.render(message.message)" />
      </div>
    </div>

    <div
      class="fixed bottom-0 transition-[left] duration-300 ease-in-out px-6 pb-4 bg-background"
      :style="{ left: isMobile ? '0' : sidebarWidth, right: '0' }"
    >
      <div class="w-full space-y-2">
        <div class="flex gap-2">
          <div class="w-50 min-w-0 max-w-50 overflow-hidden">
            <FormField
              v-slot="{ componentField }"
              name="ai_provider"
            >
              <FormItem class="space-y-0">
                <C8Select
                  :options="configuredAIProviderOptions"
                  placeholder="Select AI provider"
                  container-class="space-y-0"
                  trigger-class="h-9 w-full"
                  v-bind="componentField"
                />
                <FormMessage />
              </FormItem>
            </FormField>
          </div>

          <div class="w-50 min-w-0 max-w-50 overflow-hidden">
            <FormField
              v-slot="{ componentField }"
              name="models"
            >
              <FormItem class="space-y-0">
                <div class="w-full overflow-hidden">
                  <C8Combobox
                    v-bind="componentField"
                    :options="getProviderModels(selectedProviderId)"
                    :multiple="false"
                  />
                </div>
                <FormMessage />
              </FormItem>
            </FormField>
          </div>
        </div>
        <Textarea
          v-model="currentMessage"
          placeholder="Message"
          class="max-h-40 overflow-y-auto resize-none"
          @keydown.enter="send"
        />
        <div class="flex gap-4 items-end">
          <div
            class="flex gap-4 items-end flex-1 justify-between"
          >
            <FormField
              v-slot="{ componentField }"
              name="send_to_user"
            >
              <FormItem class="space-y-0 flex items-center space-x-2 self-center">
                <Checkbox
                  id="sendToUser"
                  :default-value="true"
                  v-bind="componentField"
                />
                <div class="grid gap-1">
                  <Label for="sendToUser">Send to Participant</Label>
                  <p
                    v-if="form.values.send_to_user"
                    class="text-muted-foreground text-sm"
                  >
                    Message will be forwarded to the participant.
                  </p>
                  <p
                    v-else
                    class="text-muted-foreground text-sm"
                  >
                    Message will be processed by AI model only.
                  </p>
                </div>
              </FormItem>
            </FormField>

            <C8Button
              label="Send"
              :disabled="disabled"
              :loading="isSubmitting"
              type="submit"
              @click="send"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'
import MarkdownIt from 'markdown-it'

import { Textarea } from '@/components/ui/textarea'
import { NEW_CHAT, NEW_MESSAGE_UPDATE } from '~/lib/consts'
import { useSidebar } from '@/components/ui/sidebar'
import { SIDEBAR_WIDTH } from '~/components/ui/sidebar/utils'
import { Send } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { computed, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import C8Select from '~/components/C8Select.vue'
import { FormField, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import C8Combobox from '~/components/C8Combobox.vue'
import C8Button from '~/components/C8Button.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'

const route = useRoute()
const { chatroomId } = route.params

const userStore = useUserStore()
const liveUpdateStore = useLiveUpdateStore()
const chatroomsStore = useChatroomStore()
const chatroomMessagesStore = useChatroomMessagesStore()
const appStore = useApplicationsStore()
const AIProviderStore = useAIProviderStore()
const AIProviderModelsStore = useAIProviderModelsStore()

const messages = computed(() => chatroomMessagesStore.messages)
const selectedApp = computed(() => appStore.selectedApplication)
const selectedChatroom = computed(() => chatroomMessagesStore.selectedChatroom)
const selectedProviderId = computed(() => form.values.ai_provider ? parseInt(form.values.ai_provider) : 0)

const currentMessage = ref('')

const { state, isMobile } = useSidebar()

const md = new MarkdownIt()

const sidebarWidth = computed(() =>
  state.value === 'expanded' ? SIDEBAR_WIDTH : '0rem',
)

const { apiError, handleError, clearError } = useApiErrorHandling()

const schema = z.object({
  ai_provider: z.string().min(1, { message: 'Please select an AI provider' }),
  models: z.array(z.string()).min(1, { message: 'Please select a model' }),
  send_to_participant: z.boolean(),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    ai_provider: undefined as string | undefined,
    models: [] as string[],
    message: undefined as string | undefined,
    send_to_user: false as boolean | false
  } as {
    ai_provider: string | undefined
    models: string[]
    message: string | undefined
    send_to_user: boolean | false
  }
})

const { isSubmitting } = form

const disabled = computed(() => {
  const values = form.values
  return !(
    (values.ai_provider as string)
    && (values.models as string[]).length > 0
  )
})

const isMessageSentByCurrentUser = (sender: string) => {
  return sender === userStore.userIdentifier
}

const configuredAIProviderOptions = computed(() =>
  AIProviderStore.AIProviders.map(p => ({
    label: p.name,
    value: p.id.toString(),
    icon: useAIProviderIcon(p.provider).value,
  })),
)

const getProviderModels = (providerId: number) => {
  const providerWithModels = AIProviderModelsStore.providerModels.find(
    pm => pm.ai_provider.id === providerId,
  )

  if (!providerWithModels?.ai_provider_models?.models_data) {
    return []
  }

  return providerWithModels.ai_provider_models.models_data.map((model) => {
    const modelName = model.name || model.displayName || model.id || Object.values(model)[0] || ''
    return {
      label: modelName.startsWith('models/') ? modelName.substring(7) : modelName,
      value: modelName,
    }
  })
}

async function send() {
  if (!currentMessage.value.trim() || !selectedApp?.value?.uuid) return

  const response = await chatroomMessagesStore.sendMessage(
    selectedApp.value.uuid,
    currentMessage.value,
    form.values.send_to_user,
    selectedProviderId.value,
    form.values.models?.[0]
  )
  currentMessage.value = ''

  if (selectedChatroom?.value?.uuid === NEW_CHAT) {
    const newChatroomId = response?.chatroom_identifier
    if (newChatroomId) {
      await navigateTo(
        `/applications/${selectedApp.value.uuid}/messages/${newChatroomId}`,
      )
      await chatroomsStore.fetchChatrooms(selectedApp.value.uuid)
    }
  }
}

const unsubscribe = liveUpdateStore.subscribe((msg) => {
  if (msg.type === NEW_MESSAGE_UPDATE && msg.data.chatroom_identifier === chatroomId) {
    chatroomMessagesStore.addMessage(msg.data)
  }
})

onBeforeUnmount(() => {
  unsubscribe()
})

onMounted(async () => {
  try {
    await AIProviderStore.load()
    await AIProviderModelsStore.load()
  }
  catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load initial data')
  }
})
</script>
