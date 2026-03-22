<template>
  <div class="flex flex-col">
    <div
      class="overflow-y-auto pt-[72px] pb-[120px] px-6 space-y-6"
      :style="`height: calc(100vh - 64px - 112px);`"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        :class="cn('flex gap-3 items-start', isCurrentUser(message.sender_identifier) ? 'flex-row-reverse' : 'flex-row')"
      >
        <div class="flex-shrink-0 mt-1">
          <div
            v-if="isLLMAgent(message.sender_identifier)"
            class="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900 flex items-center justify-center"
          >
            <Bot class="w-4 h-4 text-violet-600 dark:text-violet-300" />
          </div>
          <div
            v-else-if="isRegisteredUser(message.sender_identifier)"
            class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center"
          >
            <UserRound class="w-4 h-4 text-blue-600 dark:text-blue-300" />
          </div>
          <div
            v-else
            class="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center"
          >
            <Globe class="w-4 h-4 text-emerald-600 dark:text-emerald-300" />
          </div>
        </div>

        <!-- Bubble -->
        <div
          class="flex flex-col gap-1 max-w-[70%] lg:max-w-[60%] xl:max-w-[50%]"
          :class="isCurrentUser(message.sender_identifier) ? 'items-end' : 'items-start'"
        >
          <span class="text-xs text-muted-foreground px-1">{{ message.sender_identifier }}</span>
          <div
            :class="cn(
              'rounded-lg px-3 py-2 text-sm',
              isCurrentUser(message.sender_identifier)
                ? 'bg-primary text-primary-foreground'
                : isLLMAgent(message.sender_identifier)
                  ? 'bg-violet-50 dark:bg-violet-950 border border-violet-200 dark:border-violet-800'
                  : 'bg-muted',
            )"
          >
            <div v-html="md.render(message.message)" />
          </div>
          <div class="flex items-center gap-1 px-1">
            <template v-if="message.ai_provider_id && message.model">
              <component
                :is="useAIProviderIcon(getMessageProvider(message.ai_provider_id)?.provider ?? '').value"
                class="w-3 h-3 shrink-0"
              />
            </template>
            <span class="text-xs text-muted-foreground whitespace-nowrap">
              <template v-if="message.ai_provider_id && message.model">{{ getMessageProvider(message.ai_provider_id)?.name }} · {{ message.model.startsWith('models/') ? message.model.substring(7) : message.model }} · </template>{{ new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
            </span>
            <span
              v-if="message.is_internal"
              class="text-xs bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 rounded px-1 py-0.5 whitespace-nowrap"
            >internal</span>
          </div>
        </div>
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
                @keydown="handleMessageKeydown"
              />
              <FormMessage />
            </FormItem>
          </FormField>
          <div class="flex gap-4 items-end">
            <div
              class="flex gap-4 items-end flex-1 justify-between"
            >
              <div class="flex items-center gap-4">
                <FormField
                  v-slot="{ componentField, handleChange }"
                  type="checkbox"
                  name="is_internal"
                  :unchecked-value="false"
                >
                  <FormItem class="space-y-0 flex items-center space-x-2 self-center">
                    <Switch
                      id="isInternal"
                      v-bind="componentField"
                      @update:checked="handleChange"
                    />
                    <div class="grid gap-0.5">
                      <Label for="isInternal">Visibility</Label>
                      <p class="text-muted-foreground text-xs">
                        {{ form.values.is_internal ? 'Internal note (team only)' : 'Visible to all participants' }}
                      </p>
                    </div>
                  </FormItem>
                </FormField>

                <FormField
                  v-slot="{ componentField, handleChange }"
                  type="checkbox"
                  name="ai_mode"
                  :unchecked-value="false"
                >
                  <FormItem class="space-y-0 flex items-center space-x-2 self-center">
                    <Switch
                      id="aiMode"
                      v-bind="componentField"
                      :disabled="!form.values.is_internal"
                      @update:checked="handleChange"
                    />
                    <div class="grid gap-0.5">
                      <Label for="aiMode">AI Behavior</Label>
                      <p
                        v-if="form.values.is_internal"
                        class="text-muted-foreground text-xs"
                      >
                        {{ form.values.ai_mode ? 'This will trigger an AI response' : 'This won’t trigger an AI response' }}
                      </p>
                      <p
                        v-else
                        class="text-muted-foreground text-xs"
                      >
                        AI replies are disabled for public messages
                      </p>
                    </div>
                  </FormItem>
                </FormField>
              </div>

              <C8Button
                label="Send"
                :disabled="disabled"
                :loading="isSubmitting"
                type="submit"
                :icon="Send"
                icon-position="right"
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
import { Send, Bot, UserRound, Globe } from 'lucide-vue-next'
import { computed, onMounted, watch } from 'vue'
import { toast } from 'vue-sonner'
import C8Select from '~/components/C8Select.vue'
import { FormField, FormItem, FormMessage } from '~/components/ui/form'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
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

const { state, isMobile } = useSidebar()

const md = new MarkdownIt()

const sidebarWidth = computed(() =>
  state.value === 'expanded' ? SIDEBAR_WIDTH : '0rem',
)

const { apiError, handleError, clearError } = useApiErrorHandling()

const schema = z.object({
  ai_provider: z.string().min(1, { message: 'Please select an AI provider' }),
  models: z.array(z.string()).min(1, { message: 'Please select a model' }),
  is_internal: z.boolean(),
  ai_mode: z.boolean(),
  message: z.string().min(1, { message: 'Please enter a message' }),
  sender_identifier: z.string(),
  chatroom_identifier: z.string(),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    ai_provider: undefined as string | undefined,
    models: [] as string[],
    is_internal: false as boolean,
    ai_mode: false as boolean,
    message: '',
    sender_identifier: userStore.userIdentifier,
    chatroom_identifier: chatroomId as string,
  } as {
    ai_provider: string | undefined
    models: string[]
    is_internal: boolean
    ai_mode: boolean
    message: string
    sender_identifier: string
    chatroom_identifier: string
  }
})

const { isSubmitting } = form

const selectedProviderId = computed(() => form.values.ai_provider ? parseInt(form.values.ai_provider) : 0)

watch(() => form.values.is_internal, (isInternal) => {
  if (!isInternal) {
    form.setFieldValue('ai_mode', false)
  }
})

const disabled = computed(() => {
  const values = form.values
  return !(
    values.ai_provider?.trim()
    && (values.models as string[])?.length > 0
    && values.message?.trim()
  )
})

const isCurrentUser = (sender: string) => sender === userStore.userIdentifier
const isLLMAgent = (sender: string) => sender.startsWith('agent_llm')
const isRegisteredUser = (sender: string) => sender.startsWith('dashboard_')
const getMessageProvider = (ai_provider_id: number | null) => {
  if (!ai_provider_id) return null
  return AIProviderStore.AIProviders.find(p => p.id === ai_provider_id) ?? null
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
      values.is_internal,
      selectedProviderId.value,
      values.models?.[0],
      values.ai_mode,
    )
    form.setFieldValue('message', '')

    const targetChatroomId = response?.chatroom_identifier ?? chatroomId as string
    chatroomsStore.updateLastMessage(targetChatroomId, {
      id: Date.now(),
      uuid: response?.uuid ?? '',
      sender_identifier: userStore.userIdentifier,
      message: values.message,
      metadata: {},
      created_at: new Date().toISOString(),
      is_internal: values.is_internal,
      ai_mode: values.ai_mode,
      ai_provider_id: selectedProviderId.value,
      model: values.models?.[0],
    })

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

const handleMessageKeydown = (e: KeyboardEvent) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault()
    send()
  }
}

const unsubscribe = liveUpdateStore.subscribe((msg) => {
  if (msg.type === NEW_MESSAGE_UPDATE && msg.data.chatroom_identifier) {
    if (msg.data.chatroom_identifier === chatroomId) {
      chatroomMessagesStore.addMessage(msg.data)
    } else {
      chatroomsStore.markUnread(msg.data.chatroom_identifier)
    }
  }
})

onBeforeUnmount(() => {
  unsubscribe()
})

const getLastMessageFromCurrentUser = () => {
  const currentUserMessages = messages.value.filter(msg =>
    msg.sender_identifier === userStore.userIdentifier
  )
  return currentUserMessages.length > 0 ? currentUserMessages[currentUserMessages.length - 1] : null
}

const setFormValuesFromLastMessage = () => {
  const lastMessage = getLastMessageFromCurrentUser()
  if (lastMessage) {
    form.setFieldValue('is_internal', lastMessage.is_internal || false)
    form.setFieldValue('ai_mode', lastMessage.ai_mode || false)
  }
}

onMounted(async () => {
  chatroomsStore.markRead(chatroomId as string)
  if (selectedApp.value?.uuid && chatroomId && chatroomId !== 'new_chat') {
    await chatroomMessagesStore.selectChatroom(selectedApp.value.uuid, chatroomId as string)
  }
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

    setFormValuesFromLastMessage()
  }
  catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load initial data')
  }
})
</script>
