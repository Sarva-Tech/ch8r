<template>
  <div class="flex flex-col">
    <div
      ref="messagesContainer"
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
            class="w-8 h-8 rounded-full bg-secondary flex items-center justify-center"
          >
            <Bot class="w-4 h-4 text-secondary-foreground" />
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

        <div
          class="flex flex-col gap-1 max-w-[70%] lg:max-w-[60%] xl:max-w-[50%]"
          :class="isCurrentUser(message.sender_identifier) ? 'items-end' : 'items-start'"
        >
          <span class="text-xs text-muted-foreground px-1">{{ message.sender_identifier }}</span>

          <div
            :class="cn(
              'rounded-lg px-3 py-2 text-sm overflow-hidden',
              isCurrentUser(message.sender_identifier)
                ? 'bg-primary text-primary-foreground'
                : isLLMAgent(message.sender_identifier)
                  ? 'bg-secondary text-secondary-foreground border border-border'
                  : 'bg-muted',
            )"
          >
            <div
              class="overflow-x-auto max-w-full"
              v-html="md.render(preprocessMarkdown(message.message))"
            />
          </div>

          <div
            v-if="(message.metadata?.tool_calls as ToolCall[])?.length > 0"
            class="px-1 mt-1"
          >
            <Popover>
              <PopoverTrigger as-child>
                <button class="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground border border-border rounded-md px-2 py-1 bg-muted/40 hover:bg-muted transition-colors">
                  <Hammer class="w-3.5 h-3.5" />
                  <span>Tools</span>
                  <span class="opacity-50">({{ (message.metadata.tool_calls as ToolCall[]).length }})</span>
                </button>
              </PopoverTrigger>
              <PopoverContent
                class="w-[480px] max-h-[480px] overflow-y-auto p-0"
                align="start"
              >
                <div class="px-4 py-3 border-b border-border flex items-center gap-2">
                  <Hammer class="w-4 h-4 text-muted-foreground" />
                  <span class="text-sm font-medium">Tool Calls</span>
                  <span class="text-xs text-muted-foreground ml-auto">{{ (message.metadata.tool_calls as ToolCall[]).length }} call{{ (message.metadata.tool_calls as ToolCall[]).length > 1 ? 's' : '' }}</span>
                </div>
                <div class="divide-y divide-border">
                  <div
                    v-for="(tool, tIdx) in (message.metadata.tool_calls as ToolCall[])"
                    :key="tIdx"
                    class="px-4 py-3 space-y-3"
                  >
                    <div class="flex items-center gap-2">
                      <span class="font-mono text-sm font-medium text-foreground">{{ tool.name }}</span>
                      <div class="ml-auto flex items-center gap-2 shrink-0">
                        <span class="inline-flex items-center gap-1 text-xs text-muted-foreground">
                          <Timer class="w-3 h-3" />
                          {{ tool.duration_ms }}ms
                        </span>
                        <span
                          v-if="!tool.error"
                          class="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium"
                        >
                          <CheckCircle2 class="w-3.5 h-3.5" />
                          success
                        </span>
                        <span
                          v-else
                          class="inline-flex items-center gap-1 text-xs text-red-500 font-medium"
                        >
                          <XCircle class="w-3.5 h-3.5" />
                          failed
                        </span>
                      </div>
                    </div>

                    <div
                      v-if="tool.url"
                      class="space-y-1"
                    >
                      <p class="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                        URL
                      </p>
                      <p class="font-mono text-xs break-all text-foreground bg-muted rounded px-2 py-1.5">
                        {{ tool.url }}
                      </p>
                    </div>

                    <div
                      v-if="tool.input_parameters && Object.keys(tool.input_parameters).length"
                      class="space-y-1"
                    >
                      <p class="text-xs text-muted-foreground font-medium uppercase tracking-wide flex items-center gap-1">
                        <ArrowRight class="w-3 h-3" />
                        Input
                      </p>
                      <pre
                        class="text-xs rounded overflow-x-auto p-2 bg-muted leading-relaxed"
                        v-html="highlightJson(tool.input_parameters)"
                      />
                    </div>

                    <div
                      v-if="!tool.error && tool.raw_result"
                      class="space-y-1"
                    >
                      <p class="text-xs text-muted-foreground font-medium uppercase tracking-wide flex items-center gap-1">
                        <ArrowLeft class="w-3 h-3" />
                        Result
                      </p>
                      <pre
                        class="text-xs rounded overflow-x-auto p-2 bg-muted leading-relaxed"
                        v-html="highlightJson(tool.raw_result)"
                      />
                    </div>

                    <div
                      v-if="tool.error"
                      class="space-y-1"
                    >
                      <p class="text-xs text-red-500 font-medium uppercase tracking-wide flex items-center gap-1">
                        <XCircle class="w-3 h-3" />
                        Error
                      </p>
                      <pre class="text-xs rounded overflow-x-auto p-2 bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 leading-relaxed">{{ typeof tool.error === 'object' ? JSON.stringify(tool.error, null, 2) : tool.error }}</pre>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          <div class="flex items-center gap-1.5 px-1 flex-wrap">
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
              v-if="message.ai_mode && message.is_internal"
              class="text-xs bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 rounded px-1 py-0.5 whitespace-nowrap"
            >internal</span>
            <Popover v-if="!isLLMAgent(message.sender_identifier) && message.metadata?.escalation">
              <PopoverTrigger as-child>
                <button class="text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded px-1 py-0.5 whitespace-nowrap hover:bg-red-200 dark:hover:bg-red-800 transition-colors">
                  escalated
                </button>
              </PopoverTrigger>
              <PopoverContent
                class="w-72 p-3 space-y-2"
                align="start"
              >
                <p class="text-xs font-medium text-foreground">
                  Escalation reason
                </p>
                <p class="text-xs text-muted-foreground leading-relaxed">
                  {{ (message.metadata.reason_for_escalation as string) || 'No reason provided.' }}
                </p>
                <template v-if="(message.metadata.notified_profiles as any[])?.length > 0">
                  <p class="text-xs font-medium text-foreground pt-1">
                    Notifications sent to
                  </p>
                  <div class="space-y-1">
                    <div
                      v-for="profile in (message.metadata.notified_profiles as any[])"
                      :key="typeof profile === 'string' ? profile : profile.name"
                      class="flex items-center gap-1.5 text-xs text-muted-foreground"
                    >
                      <component
                        :is="useNotificationProviderIcon(typeof profile === 'string' ? profile : profile.type).value"
                        class="w-3 h-3 shrink-0"
                      />
                      <span>{{ typeof profile === 'string' ? profile : profile.name }}</span>
                      <span
                        v-if="typeof profile !== 'string'"
                        class="capitalize opacity-60"
                      >({{ profile.type }})</span>
                    </div>
                  </div>
                </template>
              </PopoverContent>
            </Popover>

            <Popover v-if="!isLLMAgent(message.sender_identifier) && message.metadata?.sentiment_score !== undefined">
              <PopoverTrigger as-child>
                <button class="text-xs text-muted-foreground hover:text-foreground transition-colors px-1 py-0.5 rounded hover:bg-muted">
                  <BarChart2 class="w-3 h-3" />
                </button>
              </PopoverTrigger>
              <PopoverContent
                class="w-72 p-3 space-y-3"
                align="start"
              >
                <p class="text-xs font-medium text-foreground">
                  Message analysis
                </p>
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium text-foreground">
                        Sentiment
                      </p>
                      <p class="text-xs text-muted-foreground">
                        <template v-if="(message.metadata.sentiment_score as number) > 60">
                          User seems positive or satisfied
                        </template>
                        <template v-else-if="(message.metadata.sentiment_score as number) >= 40">
                          User tone is neutral or mixed
                        </template>
                        <template v-else>
                          User appears frustrated or upset
                        </template>
                      </p>
                    </div>
                    <span class="text-xs font-medium tabular-nums ml-3 shrink-0">{{ message.metadata.sentiment_score }}/100</span>
                  </div>
                  <div class="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="(message.metadata.sentiment_score as number) > 60 ? 'bg-green-500' : (message.metadata.sentiment_score as number) >= 40 ? 'bg-yellow-500' : 'bg-red-500'"
                      :style="`width: ${message.metadata.sentiment_score}%`"
                    />
                  </div>
                </div>
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium text-foreground">
                        Escalation need
                      </p>
                      <p class="text-xs text-muted-foreground">
                        <template v-if="(message.metadata.escalation_score as number) >= 70">
                          Needs human agent — escalation triggered
                        </template>
                        <template v-else-if="(message.metadata.escalation_score as number) >= 40">
                          May need human follow-up soon
                        </template>
                        <template v-else>
                          AI can handle this without escalation
                        </template>
                      </p>
                    </div>
                    <span class="text-xs font-medium tabular-nums ml-3 shrink-0">{{ message.metadata.escalation_score }}/100</span>
                  </div>
                  <div class="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="(message.metadata.escalation_score as number) >= 70 ? 'bg-red-500' : (message.metadata.escalation_score as number) >= 40 ? 'bg-yellow-500' : 'bg-green-500'"
                      :style="`width: ${message.metadata.escalation_score}%`"
                    />
                  </div>
                </div>
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium text-foreground">
                        Criticality
                      </p>
                      <p class="text-xs text-muted-foreground">
                        <template v-if="(message.metadata.criticality_score as number) >= 70">
                          Critical issue — blocking or data loss risk
                        </template>
                        <template v-else-if="(message.metadata.criticality_score as number) >= 40">
                          Moderate issue with a workaround available
                        </template>
                        <template v-else>
                          Minor issue or general question
                        </template>
                      </p>
                    </div>
                    <span class="text-xs font-medium tabular-nums ml-3 shrink-0">{{ message.metadata.criticality_score }}/100</span>
                  </div>
                  <div class="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="(message.metadata.criticality_score as number) >= 70 ? 'bg-red-500' : (message.metadata.criticality_score as number) >= 40 ? 'bg-yellow-500' : 'bg-green-500'"
                      :style="`width: ${message.metadata.criticality_score}%`"
                    />
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            <Popover v-if="message.ai_mode && message.metadata?.usage">
              <PopoverTrigger as-child>
                <button class="text-xs text-muted-foreground hover:text-foreground transition-colors px-1 py-0.5 rounded hover:bg-muted">
                  <Cpu class="w-3 h-3" />
                </button>
              </PopoverTrigger>
              <PopoverContent
                class="w-52 p-3 space-y-2"
                align="start"
              >
                <p class="text-xs font-medium text-foreground">
                  Token usage
                </p>
                <div class="space-y-1.5 text-xs">
                  <div
                    v-if="(message.metadata.usage as any).prompt_tokens !== undefined"
                    class="flex justify-between"
                  >
                    <span class="text-muted-foreground">Prompt</span>
                    <span class="tabular-nums font-medium">{{ (message.metadata.usage as any).prompt_tokens.toLocaleString() }}</span>
                  </div>
                  <div
                    v-if="(message.metadata.usage as any).completion_tokens !== undefined"
                    class="flex justify-between"
                  >
                    <span class="text-muted-foreground">Completion</span>
                    <span class="tabular-nums font-medium">{{ (message.metadata.usage as any).completion_tokens.toLocaleString() }}</span>
                  </div>
                  <div
                    v-if="(message.metadata.usage as any).cached_tokens !== undefined"
                    class="flex justify-between"
                  >
                    <span class="text-muted-foreground">Cached</span>
                    <span class="tabular-nums font-medium">{{ (message.metadata.usage as any).cached_tokens.toLocaleString() }}</span>
                  </div>
                  <div
                    v-if="(message.metadata.usage as any).total_tokens !== undefined"
                    class="flex justify-between border-t border-border pt-1.5 mt-1"
                  >
                    <span class="text-muted-foreground font-medium">Total</span>
                    <span class="tabular-nums font-semibold">{{ (message.metadata.usage as any).total_tokens.toLocaleString() }}</span>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </div>
    </div>

    <div
      class="fixed bottom-0 transition-[left,width] duration-300 ease-in-out px-6 pb-4 bg-background"
      :style="{ left: isMobile ? '0' : sidebarWidth, width: isMobile ? '100%' : `calc(100% - ${sidebarWidth})` }"
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
            <div class="flex gap-4 items-end flex-1 justify-between">
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
                        {{ form.values.ai_mode ? 'This will trigger an AI response' : 'This won\'t trigger an AI response' }}
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
                @click="send"
              >
                <template #icon-right>
                  <KbdGroup>
                    <Kbd>Ctrl + ⏎</Kbd>
                  </KbdGroup>
                </template>
              </C8Button>
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
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

import { Kbd, KbdGroup } from '@/components/ui/kbd'
import { Textarea } from '@/components/ui/textarea'
import { NEW_CHAT, NEW_MESSAGE_UPDATE } from '~/lib/consts'
import { useSidebar } from '@/components/ui/sidebar'
import { SIDEBAR_WIDTH } from '~/components/ui/sidebar/utils'
import { Bot, UserRound, Globe, Hammer, Timer, CheckCircle2, XCircle, ArrowRight, ArrowLeft, BarChart2, Cpu } from 'lucide-vue-next'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { toast } from 'vue-sonner'
import C8Select from '~/components/C8Select.vue'
import { FormField, FormItem, FormMessage } from '~/components/ui/form'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import C8Combobox from '~/components/C8Combobox.vue'
import C8Button from '~/components/C8Button.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { useNotificationProviderIcon } from '~/composables/useNotificationProviderIcon'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

interface ToolCall {
  name: string
  input_parameters: Record<string, unknown>
  url: string
  raw_arguments: Record<string, unknown>
  raw_result: Record<string, unknown>
  timestamp: string
  duration_ms: number
  error: string | null
}

const route = useRoute()
const { chatroomId } = route.params

const messagesContainer = ref<HTMLElement>()

const openToolCalls = ref<Set<string>>(new Set())

const highlightJson = (value: unknown): string => {
  const json = JSON.stringify(value, null, 2)
  return hljs.highlight(json, { language: 'json' }).value
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    nextTick(() => {
      messagesContainer.value?.scrollTo({
        top: messagesContainer.value.scrollHeight,
        behavior: 'smooth'
      })
    })
  }
}

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

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
  typographer: true,
  html: true,
  highlight: function (str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  }
})

const preprocessMarkdown = (text: string) => {
  let processed = text
  const protectedTexts: string[] = []

  processed = processed.replace(/```[\s\S]*?```/g, (match) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`
    protectedTexts.push(match)
    return placeholder
  })

  processed = processed.replace(/`[^`]+`/g, (match) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`
    protectedTexts.push(match)
    return placeholder
  })

  processed = processed.replace(/\*\*([^*]+)\*\*/g, (match, content) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`
    protectedTexts.push(`**${content}**`)
    return placeholder
  })

  processed = processed.replace(/\b\w+-\w+\b/g, (match) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`
    protectedTexts.push(match)
    return placeholder
  })

  processed = processed.replace(/:\s*-\s*/g, ':\n\n- ')
  processed = processed.replace(/([.!?])\s*-\s*/g, '$1\n\n- ')
  processed = processed.replace(/([a-z.!?])\s*-\s*/g, '$1\n\n- ')

  protectedTexts.forEach((content, index) => {
    processed = processed.replace(`__PROTECTED_${index}__`, content)
  })

  return processed
}

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
    is_internal: chatroomId === NEW_CHAT ? true : false as boolean,
    ai_mode: chatroomId === NEW_CHAT ? true : false as boolean,
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

    scrollToBottom()

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
    scrollToBottom()
  }
  catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load initial data')
  }
})
</script>

<style scoped>
:deep(.prose) {
  line-height: 1.6;
}

:deep(p) {
  margin-bottom: 0.75rem;
}

:deep(ul) {
  margin: 1rem 0;
  padding-left: 1.5rem;
  list-style-type: disc;
}

:deep(li) {
  margin-bottom: 0.5rem;
  line-height: 1.6;
  list-style-position: outside;
}

:deep(strong) {
  font-weight: 600;
}

:deep(h1, h2, h3, h4, h5, h6) {
  margin: 1.5rem 0 0.75rem 0;
  font-weight: 600;
}

:deep(br) {
  content: "";
  display: block;
  margin-bottom: 0.25rem;
}

:deep(pre) {
  background-color: hsl(var(--muted));
  border: 1px solid hsl(var(--border));
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 1rem 0;
  overflow-x: auto;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  max-width: 100%;
  word-wrap: break-word;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(code) {
  background-color: hsl(var(--muted));
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.875rem;
  word-wrap: break-word;
  word-break: break-word;
}

:deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
}

:deep(.hljs-keyword) {
  color: #0000ff;
  font-weight: bold;
}

:deep(.hljs-string) {
  color: #008000;
}

:deep(.hljs-comment) {
  color: #808080;
  font-style: italic;
}

:deep(.hljs-tag) {
  color: #0000ff;
}

:deep(.hljs-attr) {
  color: #ff0000;
}

/* Accordion transition */
.accordion-enter-active,
.accordion-leave-active {
  transition: opacity 0.2s ease, max-height 0.25s ease;
  max-height: 1000px;
  overflow: hidden;
}

.accordion-enter-from,
.accordion-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
