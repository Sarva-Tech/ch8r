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
        <form
          class="space-y-2"
          @submit.prevent="send"
        >
          <C8APIAlert :api-error="apiError" />
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
          <FormField
            v-slot="{ componentField }"
            name="message"
          >
            <FormItem class="space-y-0">
              <Textarea
                v-bind="componentField"
                placeholder="Message"
                class="max-h-40 overflow-y-auto resize-none"
              />
              <FormMessage />
            </FormItem>
          </FormField>
          <div class="flex gap-4 items-end">
            <div
              class="flex gap-4 items-end flex-1 justify-between"
            >
              <div class="flex items-center space-x-2 self-center">
                <Checkbox
                  id="sendToUser"
                  :checked="sendToParticipant === true"
                  @update:checked="(val) => { sendToParticipant = val === true }"
                />
                <div class="grid gap-1">
                  <Label for="sendToUser">Send to Participant</Label>
                  <p
                    v-if="sendToParticipant"
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
              </div>

              <C8Button
                label="Send"
                :disabled="disabled"
                :loading="isSubmitting"
                type="submit"
                :icon="Send"
                @click="send"
              />
            </div>
          </div>
        </form>
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
import { computed, onMounted, ref } from 'vue'
import { toast } from 'vue-sonner'
import C8Select from '~/components/C8Select.vue'
import { FormField, FormItem, FormLabel, FormMessage, FormControl } from '~/components/ui/form'
import { Checkbox } from '~/components/ui/checkbox'
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
const AppAIProviderStore = useAppAIProviderStore()

const messages = computed(() => chatroomMessagesStore.messages)
const selectedApp = computed(() => appStore.selectedApplication)
const selectedChatroom = computed(() => chatroomMessagesStore.selectedChatroom)
const lastUsedAIProvider = computed(() => chatroomMessagesStore.lastUsedAIProvider)
const lastUsedAIModel = computed(() => chatroomMessagesStore.lastUsedAIModel)
const selectedProviderId = computed(() => form.values.ai_provider ? parseInt(form.values.ai_provider) : 0)

const { state, isMobile } = useSidebar()

const md = new MarkdownIt()

const sendToParticipant = ref(false)

const sidebarWidth = computed(() =>
  state.value === 'expanded' ? SIDEBAR_WIDTH : '0rem',
)

const { apiError, handleError, clearError } = useApiErrorHandling()

const schema = z.object({
  ai_provider: z.string().min(1, { message: 'Please select an AI provider' }),
  models: z.array(z.string()).min(1, { message: 'Please select a model' }),
  send_to_participant: z.boolean(),
  message: z.string().min(1, { message: 'Please enter a message' }),
  sender_identifier: z.string(),
  chatroom_identifier: z.string(),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    ai_provider: undefined as string | undefined,
    models: [] as string[],
    send_to_participant: false as boolean,
    message: '',
    sender_identifier: userStore.userIdentifier,
    chatroom_identifier: chatroomId as string,
  } as {
    ai_provider: string | undefined
    models: string[]
    send_to_participant: boolean
    message: string
    sender_identifier: string
    chatroom_identifier: string
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

const send = form.handleSubmit(async (values) => {
  if (!selectedApp?.value?.uuid) return
  clearError()
  try {
    const response = await chatroomMessagesStore.sendMessage(
      selectedApp.value.uuid,
      values.message,
      sendToParticipant.value,
      selectedProviderId.value,
      values.models?.[0]
    )
    form.setFieldValue('message', '')

    if (selectedChatroom?.value?.uuid === NEW_CHAT) {
      const newChatroomId = response?.chatroom_identifier
      if (newChatroomId) {
        await navigateTo(
          `/applications/${selectedApp.value.uuid}/messages/${newChatroomId}`,
        )
        await chatroomsStore.fetchChatrooms(selectedApp.value.uuid)
      }
    }
  } catch (error: unknown) {
    handleError(error, form)
  }
})

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
    await AppAIProviderStore.fetchAppAIProviderConfigs(selectedApp.value.uuid)

    const lastUsedProvider = lastUsedAIProvider.value
    const appProviders = AppAIProviderStore.existingAppAIProviderConfigs

    if (lastUsedProvider) {
      form.setFieldValue('ai_provider', lastUsedProvider.id.toString())
      form.setFieldValue('models', [lastUsedAIModel.value ?? ''])
    } else {
      const responseTextProvider = appProviders.find(
        config => config.context === 'response' && config.capability === 'text'
      )
      if (responseTextProvider) {
        form.setFieldValue('ai_provider', responseTextProvider.ai_provider.id.toString())
        form.setFieldValue('models', [responseTextProvider.external_model_id ?? ''])
      }
    }
  }
  catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load initial data')
  }
})
</script>
