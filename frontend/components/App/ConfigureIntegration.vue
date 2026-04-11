<template>
  <component
    :is="props.inline ? 'div' : Card"
    :class="props.inline ? 'space-y-4' : ''"
  >
    <component
      :is="props.inline ? 'div' : CardHeader"
      :class="props.inline ? 'space-y-1' : ''"
    >
      <component
        :is="props.inline ? 'p' : CardTitle"
        :class="props.inline ? 'text-sm font-semibold' : ''"
      >
        {{ config.title }}
      </component>
      <component
        :is="props.inline ? 'p' : CardDescription"
        :class="props.inline ? 'text-xs text-muted-foreground' : ''"
      >
        {{ config.description }}
      </component>
    </component>
    <component
      :is="props.inline ? 'div' : CardContent"
      class="space-y-4"
    >
      <form
        class="space-y-4"
        @submit.prevent="save"
      >
        <C8APIAlert :api-error="apiError" />

        <template v-if="integrationStore.integrations.length === 0">
          <p class="text-sm text-muted-foreground">
            No integrations connected.
            <NuxtLink
              to="/settings/integrations"
              class="underline font-medium"
            >
              Connect one in Settings → Integrations
            </NuxtLink>.
          </p>
        </template>

        <template v-else>
          <FormField
            v-slot="{ componentField }"
            name="integration_uuid"
          >
            <FormItem>
              <FormLabel class="flex items-center">
                Integration
                <RequiredLabel />
              </FormLabel>
              <C8Select
                :options="integrationOptions"
                v-bind="componentField"
                placeholder="Select integration"
              />
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField
            v-if="config.requiresRepo"
            name="repo"
          >
            <FormItem>
              <FormLabel class="flex items-center">
                Repository
                <RequiredLabel />
              </FormLabel>
              <C8Combobox
                v-model="selectedRepo"
                :options="repoOptions"
                :multiple="false"
                :allow-custom-values="true"
                placeholder="Select or type owner/repo"
                search-placeholder="Search repositories..."
                no-results-message="No matching repos"
                :no-options-message="loadingRepos ? 'Loading repositories...' : 'Type owner/repo manually'"
                add-custom-hint="Press Enter to use this repo"
                :disabled="!form.values.integration_uuid || loadingRepos"
              />
              <FormMessage />
            </FormItem>
          </FormField>

          <template v-if="existingAppIntegration">
            <div class="border rounded-md p-3 space-y-3">
              <p class="text-sm font-medium">
                Tools
              </p>
              <div
                v-if="toolsLoading"
                class="text-xs text-muted-foreground"
              >
                Loading tools...
              </div>
              <template v-else>
                <div
                  v-for="tool in builtInTools"
                  :key="tool.tool_id"
                  class="flex items-start justify-between gap-3"
                >
                  <div class="flex-1 min-w-0">
                    <p class="text-sm">
                      {{ tool.title }}
                    </p>
                    <p class="text-xs text-muted-foreground">
                      {{ tool.description }}
                    </p>
                  </div>
                  <Switch
                    :model-value="tool.is_enabled"
                    @click="setToolEnabled(tool.tool_id, !tool.is_enabled)"
                  />
                </div>
                <div
                  v-for="ct in customTools"
                  :key="ct.uuid"
                  class="flex items-start justify-between gap-3"
                >
                  <div class="flex-1 min-w-0">
                    <p class="text-sm">
                      {{ ct.title }}
                    </p>
                    <p class="text-xs text-muted-foreground">
                      {{ ct.description }}
                    </p>
                  </div>
                  <div class="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      class="h-6 w-6"
                      @click="openEdit(ct)"
                    >
                      <Pencil class="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      class="h-6 w-6 text-destructive hover:text-destructive"
                      @click="openDeleteConfirm(ct)"
                    >
                      <Trash2 class="h-3 w-3" />
                    </Button>
                    <Switch
                      :model-value="ct.is_enabled"
                      @click="setCustomToolEnabled(ct.uuid!, !ct.is_enabled)"
                    />
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  type="button"
                  @click="openAdd"
                >
                  Add Custom Tool
                </Button>
              </template>
            </div>
          </template>

          <div class="flex justify-end">
            <C8Button
              label="Configure"
              :disabled="disabled"
              :loading="isSubmitting"
              type="submit"
            />
          </div>
        </template>
      </form>
    </component>
  </component>

  <SlideOver
    :title="customToolForm.editingUuid ? 'Edit Custom Tool' : 'Add Custom Tool'"
    :open="slideOverOpen"
    :loading="customToolForm.saving"
    @update:open="slideOverOpen = $event"
  >
    <template #submitBtn>
      <Button
        :disabled="customToolForm.saving"
        @click="submitCustomTool"
      >
        Save
      </Button>
    </template>
    <div class="space-y-4 py-4">
      <p
        v-if="customToolForm.error"
        class="text-sm text-destructive"
      >
        {{ customToolForm.error }}
      </p>
      <div class="space-y-1">
        <label class="text-sm font-medium">Title <span class="text-destructive">*</span></label>
        <Input
          v-model="customToolForm.title"
          placeholder="My Custom Tool"
        />
        <p
          v-if="customToolForm.fieldErrors.title"
          class="text-xs text-destructive"
        >
          {{ customToolForm.fieldErrors.title }}
        </p>
      </div>
      <div class="space-y-1">
        <label class="text-sm font-medium">Description <span class="text-destructive">*</span></label>
        <Textarea
          v-model="customToolForm.description"
          placeholder="Describe what this tool does"
          :rows="3"
        />
        <p
          v-if="customToolForm.fieldErrors.description"
          class="text-xs text-destructive"
        >
          {{ customToolForm.fieldErrors.description }}
        </p>
      </div>
      <div class="space-y-1">
        <label class="text-sm font-medium">URL Schema <span class="text-destructive">*</span></label>
        <Textarea
          v-model="customToolForm.urlSchema"
          placeholder="curl -X POST https://api.example.com/endpoint -H &quot;Content-Type: application/json&quot; -d '{&quot;key&quot;: &quot;value&quot;}'"
          :rows="5"
        />
        <p
          v-if="customToolForm.fieldErrors.urlSchema"
          class="text-xs text-destructive"
        >
          {{ customToolForm.fieldErrors.urlSchema }}
        </p>
      </div>
    </div>
  </SlideOver>

  <!-- Delete Confirmation -->
  <C8Dialog
    title="Delete Custom Tool"
    description="Are you sure you want to delete this custom tool? This action cannot be undone."
    confirm-text="Delete"
    :is-open="deleteConfirm.open"
    :destructive="true"
    @update:open="deleteConfirm.open = $event"
    @confirm="confirmDelete"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import { Pencil, Trash2 } from 'lucide-vue-next'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  FormItem,
  FormLabel,
  FormMessage,
  FormField,
} from '~/components/ui/form'
import { Switch } from '~/components/ui/switch'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
import { Button } from '~/components/ui/button'
import C8Select from '~/components/C8Select.vue'
import C8Combobox from '~/components/C8Combobox.vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8Button from '~/components/C8Button.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import SlideOver from '~/components/SlideOver.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { useIntegrationStore } from '~/stores/integration'
import { useAppIntegrationStore } from '~/stores/appIntegration'
import { useHttpClient } from '~/composables/useHttpClient'

interface Tool {
  uuid: string | null
  tool_id: string
  title: string
  description: string
  is_enabled: boolean
  is_builtin: boolean
  url_schema: string | null
}

interface IntegrationConfig {
  id: string
  title: string
  description: string
  requiresRepo: boolean
  successMessage: string
}

const props = defineProps<{ config: IntegrationConfig, inline?: boolean }>()

const appStore = useApplicationsStore()
const integrationStore = useIntegrationStore()
const appIntegrationStore = useAppIntegrationStore()
const { apiError, handleError, clearError } = useApiErrorHandling()
const { httpGet, httpPatch, httpPost, httpDelete } = useHttpClient()

const existingAppIntegration = ref<{ uuid: string } | null>(null)
const tools = ref<Tool[]>([])
const toolsLoading = ref(false)

const builtInTools = computed(() => tools.value.filter(t => t.is_builtin))
const customTools = computed(() => tools.value.filter(t => !t.is_builtin))

const slideOverOpen = ref(false)
const customToolForm = ref({
  editingUuid: null as string | null,
  title: '',
  description: '',
  urlSchema: '',
  saving: false,
  error: '',
  fieldErrors: { title: '', description: '', urlSchema: '' },
})

const deleteConfirm = ref({ open: false, toolUuid: '' })

const repoOptions = ref<{ value: string, label: string }[]>([])
const loadingRepos = ref(false)
const selectedRepo = ref<string[]>([])

const schema = computed(() =>
  props.config.requiresRepo
    ? z.object({
        integration_uuid: z.string().min(1, { message: 'Please select an integration' }),
        repo: z.string().optional(),
      })
    : z.object({
        integration_uuid: z.string().min(1, { message: 'Please select an integration' }),
        repo: z.string().optional(),
      }),
)

const form = useForm({
  validationSchema: toTypedSchema(schema.value),
  initialValues: { integration_uuid: '', repo: '' },
})
const { isSubmitting } = form

const integrationOptions = computed(() =>
  integrationStore.integrations.map(i => ({
    label: i.name || i.provider,
    value: i.uuid,
  })),
)

async function loadRepos(integrationUuid: string) {
  if (!integrationUuid) return
  loadingRepos.value = true
  try {
    const repos = await integrationStore.fetchRepos(integrationUuid)
    repoOptions.value = repos.map(r => ({ value: r.full_name, label: r.full_name }))
  }
  catch (e) {
    console.error('Failed to load repos', e)
  }
  finally {
    loadingRepos.value = false
  }
}

watch(() => form.values.integration_uuid, (uuid) => {
  if (uuid && props.config.requiresRepo) {
    // Only clear repos if the integration actually changed
    repoOptions.value = []
    loadRepos(uuid)
  }
}, { immediate: false })

watch(selectedRepo, (val) => {
  form.setFieldValue('repo', val[0] ?? '')
})

const disabled = computed(() => {
  const v = form.values
  if (!v.integration_uuid?.trim()) return true
  if (props.config.requiresRepo && !selectedRepo.value[0]?.trim()) return true
  return false
})

onMounted(async () => {
  try {
    await integrationStore.load()
    const appUuid = appStore.selectedApplication?.uuid
    if (appUuid) {
      await appIntegrationStore.load(appUuid)
      const existing = appIntegrationStore.appIntegrations.find(
        ai => ai.integration_type === props.config.id,
      )
      if (existing) {
        existingAppIntegration.value = existing
        form.setFieldValue('integration_uuid', existing.integration.uuid)
        if (props.config.requiresRepo) {
          const existingRepo = (existing.metadata?.repo as string) ?? ''
          selectedRepo.value = existingRepo ? [existingRepo] : []
          form.setFieldValue('repo', existingRepo)
          await loadRepos(existing.integration.uuid)
        }
        await loadTools(appUuid, existing.uuid)
      }
    }
  }
  catch (e) {
    console.error(e)
  }
})

const save = form.handleSubmit(async (values) => {
  clearError()
  const appUuid = appStore.selectedApplication?.uuid
  if (!appUuid) return
  try {
    const toolsPayload = builtInTools.value.length > 0
      ? Object.fromEntries(builtInTools.value.map(t => [t.tool_id, { is_enabled: t.is_enabled }]))
      : undefined

    const customToolsPayload = customTools.value
      .filter(t => t.uuid !== null)
      .map(t => ({ uuid: t.uuid, is_enabled: t.is_enabled }))
    const result = await appIntegrationStore.create(appUuid, {
      integration_uuid: values.integration_uuid,
      integration_type: props.config.id,
      metadata: props.config.requiresRepo ? { repo: values.repo } : {},
      ...(toolsPayload ? { tools: toolsPayload } : {}),
      ...(customToolsPayload.length > 0 ? { custom_tools: customToolsPayload } : {}),
    })
    existingAppIntegration.value = result
    toast.success(props.config.successMessage)
    await loadTools(appUuid, result.uuid)
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})

async function loadTools(appUuid: string, integrationUuid: string) {
  toolsLoading.value = true
  try {
    tools.value = await httpGet<Tool[]>(`/applications/${appUuid}/integrations/${integrationUuid}/tools/`)
  }
  catch (e) {
    console.error('Failed to load tools', e)
  }
  finally { toolsLoading.value = false }
}

function setToolEnabled(toolId: string, val: boolean) {
  const idx = tools.value.findIndex(t => t.tool_id === toolId)
  if (idx !== -1) tools.value[idx] = { ...tools.value[idx], is_enabled: val }
}

function setCustomToolEnabled(uuid: string, val: boolean) {
  const idx = tools.value.findIndex(t => t.uuid === uuid)
  if (idx !== -1) tools.value[idx] = { ...tools.value[idx], is_enabled: val }
}

function resetForm() {
  customToolForm.value = { editingUuid: null, title: '', description: '', urlSchema: '', saving: false, error: '', fieldErrors: { title: '', description: '', urlSchema: '' } }
}

function openAdd() { resetForm(); slideOverOpen.value = true }

function openEdit(ct: Tool) {
  resetForm()
  customToolForm.value.editingUuid = ct.uuid
  customToolForm.value.title = ct.title
  customToolForm.value.description = ct.description
  customToolForm.value.urlSchema = ct.url_schema ?? ''
  slideOverOpen.value = true
}

function validateForm(): boolean {
  const fe = customToolForm.value.fieldErrors
  fe.title = customToolForm.value.title.trim() ? '' : 'Required'
  fe.description = customToolForm.value.description.trim() ? '' : 'Required'
  fe.urlSchema = customToolForm.value.urlSchema.trim() ? '' : 'Required'
  return !fe.title && !fe.description && !fe.urlSchema
}

async function submitCustomTool() {
  if (!validateForm()) return
  const appUuid = appStore.selectedApplication?.uuid
  const integrationUuid = existingAppIntegration.value?.uuid
  if (!appUuid || !integrationUuid) return
  customToolForm.value.saving = true
  customToolForm.value.error = ''
  const payload = { title: customToolForm.value.title.trim(), description: customToolForm.value.description.trim(), url_schema: customToolForm.value.urlSchema.trim() }
  try {
    if (customToolForm.value.editingUuid) {
      const updated = await httpPatch<Tool>(`/applications/${appUuid}/integrations/${integrationUuid}/tools/${customToolForm.value.editingUuid}/`, payload)
      const idx = tools.value.findIndex(t => t.uuid === customToolForm.value.editingUuid)
      if (idx !== -1) tools.value[idx] = updated
      toast.success('Custom tool updated')
    }
    else {
      const created = await httpPost<Tool>(`/applications/${appUuid}/integrations/${integrationUuid}/tools/`, payload)
      tools.value.push(created)
      toast.success('Custom tool added')
    }
    slideOverOpen.value = false
  }
  catch (err: unknown) {
    customToolForm.value.error = (err as { message?: string })?.message ?? 'An error occurred'
  }
  finally { customToolForm.value.saving = false }
}

function openDeleteConfirm(ct: Tool) {
  deleteConfirm.value = { open: true, toolUuid: ct.uuid! }
}

async function confirmDelete() {
  const appUuid = appStore.selectedApplication?.uuid
  const integrationUuid = existingAppIntegration.value?.uuid
  if (!appUuid || !integrationUuid) return
  try {
    await httpDelete(`/applications/${appUuid}/integrations/${integrationUuid}/tools/${deleteConfirm.value.toolUuid}/`)
    tools.value = tools.value.filter(t => t.uuid !== deleteConfirm.value.toolUuid)
    toast.success('Custom tool deleted')
  }
  catch { toast.error('Failed to delete custom tool') }
  finally { deleteConfirm.value.open = false }
}
</script>
