<template>
  <Card>
    <CardHeader>
      <CardTitle>Agent Configuration</CardTitle>
      <CardDescription>
        Define your agent's persona, tone, and response style.
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <!-- Persona + Task -->
      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-2">
          <Label for="role">Persona</Label>
          <Select v-model="role">
            <SelectTrigger id="role" class="!w-full">
              <SelectValue placeholder="Select persona" />
            </SelectTrigger>
            <SelectContent class="w-[var(--reka-select-trigger-width)]">
              <SelectItem v-for="preset in ROLE_PRESETS" :key="preset.value" :value="preset.value">
                {{ preset.label }}
              </SelectItem>
              <SelectItem value="custom">Custom...</SelectItem>
            </SelectContent>
          </Select>
          <Input
            v-if="role === 'custom'"
            v-model="customRole"
            maxlength="200"
            placeholder="Enter a custom persona..."
          />
        </div>

        <div class="space-y-2">
          <Label for="behavior">Task</Label>
          <Select v-model="behavior">
            <SelectTrigger id="behavior" class="!w-full">
              <SelectValue placeholder="Select task" />
            </SelectTrigger>
            <SelectContent class="w-[var(--reka-select-trigger-width)]">
              <SelectItem v-for="preset in BEHAVIOR_PRESETS" :key="preset.value" :value="preset.value">
                {{ preset.label }}
              </SelectItem>
              <SelectItem value="custom">Custom...</SelectItem>
            </SelectContent>
          </Select>
          <Input
            v-if="behavior === 'custom'"
            v-model="customBehavior"
            maxlength="500"
            placeholder="Enter a custom task..."
          />
        </div>
      </div>

      <!-- Tone + Response Style -->
      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-2">
          <Label for="tone">Tone</Label>
          <Select v-model="tone">
            <SelectTrigger id="tone" class="!w-full">
              <SelectValue placeholder="Select tone" />
            </SelectTrigger>
            <SelectContent class="w-[var(--reka-select-trigger-width)]">
              <SelectItem value="professional">Professional</SelectItem>
              <SelectItem value="friendly">Friendly</SelectItem>
              <SelectItem value="formal">Formal</SelectItem>
              <SelectItem value="casual">Casual</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <Label for="response-style">Response Style</Label>
          <Select v-model="responseStyle">
            <SelectTrigger id="response-style" class="!w-full">
              <SelectValue placeholder="Select response style" />
            </SelectTrigger>
            <SelectContent class="w-[var(--reka-select-trigger-width)]">
              <SelectItem value="balanced">Balanced</SelectItem>
              <SelectItem value="concise">Concise</SelectItem>
              <SelectItem value="detailed">Detailed</SelectItem>
              <SelectItem value="step_by_step">Step-by-Step</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <!-- Custom Instructions -->
      <div class="space-y-2">
        <Label for="custom-instructions">Custom Instructions</Label>
        <Textarea
          id="custom-instructions"
          v-model="customInstructions"
          maxlength="1000"
          placeholder="Enter any custom instructions..."
          class="resize-none"
          rows="4"
        />
        <p class="text-muted-foreground text-xs text-right">
          {{ customInstructions.length }} / 1000
        </p>
      </div>
    </CardContent>
    <CardFooter class="flex justify-end">
      <C8Button
        label="Save"
        :disabled="processing"
        :loading="processing"
        @click="save"
      />
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { PromptConfig } from '~/stores/configureApp'

const ROLE_PRESETS: { label: string; value: string }[] = [
  { label: 'Customer Service Assistant', value: 'customer service assistant' },
  { label: 'Project Manager', value: 'project manager' },
  { label: 'Technical Support Specialist', value: 'technical support specialist' },
  { label: 'Sales Assistant', value: 'sales assistant' },
  { label: 'HR Assistant', value: 'HR assistant' },
]

const BEHAVIOR_PRESETS: { label: string; value: string }[] = [
  { label: 'Answer User Questions Politely and Competently', value: 'answer user questions politely and competently' },
  { label: 'Manage Project Tasks and Timelines', value: 'manage project tasks and timelines' },
  { label: 'Troubleshoot Technical Issues Step by Step', value: 'troubleshoot technical issues step by step' },
  { label: 'Assist with Sales Inquiries and Product Information', value: 'assist with sales inquiries and product information' },
  { label: 'Handle HR Queries and Employee Support', value: 'handle HR queries and employee support' },
]

const appConfigStore = useAppConfigurationStore()
const processing = ref(false)

const tone = ref<PromptConfig['tone']>('professional')
const responseStyle = ref<PromptConfig['response_style']>('balanced')
const customInstructions = ref('')
const role = ref<string>(ROLE_PRESETS[0])
const customRole = ref('')
const behavior = ref<string>(BEHAVIOR_PRESETS[0])
const customBehavior = ref('')

onMounted(() => {
  tone.value = appConfigStore.promptConfig.tone
  responseStyle.value = appConfigStore.promptConfig.response_style
  customInstructions.value = appConfigStore.promptConfig.custom_instructions

  const storedRole = appConfigStore.promptConfig.role
  if (ROLE_PRESETS.some(p => p.value === storedRole)) {
    role.value = storedRole
  } else {
    role.value = 'custom'
    customRole.value = storedRole
  }

  const storedBehavior = appConfigStore.promptConfig.behavior
  if (BEHAVIOR_PRESETS.some(p => p.value === storedBehavior)) {
    behavior.value = storedBehavior
  } else {
    behavior.value = 'custom'
    customBehavior.value = storedBehavior
  }
})

async function save() {
  processing.value = true
  try {
    await appConfigStore.savePromptConfig({
      tone: tone.value,
      response_style: responseStyle.value,
      custom_instructions: customInstructions.value,
      role: role.value === 'custom' ? customRole.value : role.value,
      behavior: behavior.value === 'custom' ? customBehavior.value : behavior.value,
    })
    toast.success('Prompt configuration saved')
  } catch (e: unknown) {
    toast.error(e?.message || 'Error saving prompt configuration')
    console.error(e)
  } finally {
    processing.value = false
  }
}
</script>
