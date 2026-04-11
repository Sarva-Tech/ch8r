<template>
  <div class="space-y-6">
    <div
      v-for="type in SUPPORTED_INTEGRATION_TYPES"
      :key="type.id"
      class="space-y-4"
    >
      <h3 class="text-sm font-semibold">
        {{ type.label }}
      </h3>

      <template v-if="integrationStore.integrations.length === 0">
        <p class="text-sm text-muted-foreground">
          No integrations connected. Connect one in
          <NuxtLink
            to="/settings/integrations"
            class="underline"
          >
            Settings → Integrations
          </NuxtLink>.
        </p>
      </template>

      <template v-else>
        <C8APIAlert :api-error="sectionErrors[type.id] ?? null" />

        <C8Select
          v-model="sectionState[type.id].integrationUuid"
          label="Integration"
          placeholder="Select an integration"
          :options="integrationOptions"
        />

        <div class="space-y-2">
          <label class="text-sm font-medium">Repository</label>
          <Input
            v-model="sectionState[type.id].repo"
            placeholder="owner/repo"
          />
        </div>

        <C8Button
          label="Save"
          :loading="sectionState[type.id].saving"
          @click="save(type.id)"
        />
      </template>

      <template v-if="getExistingIntegration(type.id)">
        <div class="border-t pt-4 space-y-4">
          <div class="space-y-2">
            <h4 class="text-sm font-medium">
              Tools
            </h4>
            <p
              v-if="toolsLoading[getExistingIntegration(type.id)!.uuid]"
              class="text-sm text-muted-foreground"
            >
              Loading tools...
            </p>
            <div
              v-else
              class="space-y-2"
            >
              <div
                v-for="tool in toolsByIntegration[getExistingIntegration(type.id)!.uuid] ?? []"
                :key="tool.tool_id"
                class="flex items-start justify-between gap-4 py-2"
              >
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium">
                    {{ tool.title }}
                  </p>
                  <p class="text-xs text-muted-foreground">
                    {{ tool.description }}
                  </p>
                </div>
                <Switch
                  :checked="tool.is_enabled"
                  @update:checked="(val) => toggleBuiltInTool(getExistingIntegration(type.id)!.uuid, tool, val)"
                />
              </div>
              <p
                v-if="(toolsByIntegration[getExistingIntegration(type.id)!.uuid] ?? []).length === 0"
                class="text-sm text-muted-foreground"
              >
                No tools available for this integration.
              </p>
            </div>
          </div>

          <div class="space-y-2">
            <h4 class="text-sm font-medium">
              Custom Tools
            </h4>
            <div class="space-y-2">
              <div
                v-for="ct in customToolsByIntegration[getExistingIntegration(type.id)!.uuid] ?? []"
                :key="ct.uuid"
                class="flex items-center justify-between gap-4 py-2"
              >
                <div class="flex items-center gap-3 flex-1 min-w-0">
                  <Switch
                    :checked="ct.is_enabled"
                    @update:checked="(val) => toggleCustomTool(getExistingIntegration(type.id)!.uuid, ct, val)"
                  />
                  <span class="text-sm truncate">{{ ct.title }}</span>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-7 w-7"
                    @click="openEditCustomTool(getExistingIntegration(type.id)!.uuid, ct)"
                  >
                    <Pencil class="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-7 w-7 text-destructive hover:text-destructive"
                    @click="openDeleteConfirm(getExistingIntegration(type.id)!.uuid, ct)"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              @click="openAddCustomTool(getExistingIntegration(type.id)!.uuid)"
            >
              Add Custom Tool
            </Button>
          </div>
        </div>
      </template>
    </div>

    <SlideOver
      :title="customToolForm.editingUuid ? 'Edit Custom Tool' : 'Add Custom Tool'"
      :open="slideOverOpen"
      :loading="customToolForm.saving"
      submit-text="Save"
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
            rows="3"
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

    <C8Dialog
      title="Delete Custom Tool"
      description="Are you sure you want to delete this custom tool? This action cannot be undone."
      confirm-text="Delete"
      :is-open="deleteConfirm.open"
      :destructive="true"
      @update:open="deleteConfirm.open = $event"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import { Pencil, Trash2 } from 'lucide-vue-next'
import { useIntegrationStore } from '~/stores/integration'
import { useAppIntegrationStore } from '~/stores/appIntegration'
import { useHttpClient } from '~/composables/useHttpClient'
import C8Select from '~/components/C8Select.vue'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
import { Button } from '~/components/ui/button'
import { Switch } from '~/components/ui/switch'
import C8Button from '~/components/C8Button.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import SlideOver from '~/components/SlideOver.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'

interface BuiltInTool {
  tool_id: string
  title: string
  description: string
  is_enabled: boolean
}

interface CustomTool {
  uuid: string
  title: string
  description: string
  url_schema: string
  is_enabled: boolean
}

const SUPPORTED_INTEGRATION_TYPES = [
  { id: 'version_control', label: 'Version Control' },
  { id: 'project_management', label: 'Project Management' },
] as const

type IntegrationTypeId = typeof SUPPORTED_INTEGRATION_TYPES[number]['id']

const props = defineProps<{
  applicationUuid: string
}>()

const integrationStore = useIntegrationStore()
const appIntegrationStore = useAppIntegrationStore()
const { httpGet, httpPatch, httpPost, httpDelete } = useHttpClient()

const sectionState = ref<Record<IntegrationTypeId, { integrationUuid: string | null, repo: string, saving: boolean }>>({
  version_control: { integrationUuid: null, repo: '', saving: false },
  project_management: { integrationUuid: null, repo: '', saving: false },
})

const sectionErrors = ref<Record<string, unknown>>({
  version_control: null,
  project_management: null,
})

const integrationOptions = computed(() =>
  integrationStore.integrations.map(i => ({
    label: i.name || i.provider,
    value: i.uuid,
  })),
)

const toolsByIntegration = ref<Record<string, BuiltInTool[]>>({})
const customToolsByIntegration = ref<Record<string, CustomTool[]>>({})
const toolsLoading = ref<Record<string, boolean>>({})

const slideOverOpen = ref(false)
const customToolForm = ref({
  integrationUuid: '',
  editingUuid: null as string | null,
  title: '',
  description: '',
  urlSchema: '',
  saving: false,
  error: '',
  fieldErrors: { title: '', description: '', urlSchema: '' },
})

const deleteConfirm = ref({
  open: false,
  integrationUuid: '',
  toolUuid: '',
})

function getExistingIntegration(typeId: IntegrationTypeId) {
  return appIntegrationStore.appIntegrations.find(ai => ai.integration_type === typeId) ?? null
}

function populateFromExisting() {
  for (const type of SUPPORTED_INTEGRATION_TYPES) {
    const existing = getExistingIntegration(type.id)
    if (existing) {
      sectionState.value[type.id].integrationUuid = existing.integration.uuid
      sectionState.value[type.id].repo = (existing.metadata?.repo as string) ?? ''
    }
  }
}

async function loadToolsForIntegration(integrationUuid: string) {
  toolsLoading.value[integrationUuid] = true
  try {
    const [builtIn, custom] = await Promise.all([
      httpGet<BuiltInTool[]>(`/applications/${props.applicationUuid}/integrations/${integrationUuid}/tools/`),
      httpGet<CustomTool[]>(`/applications/${props.applicationUuid}/integrations/${integrationUuid}/custom-tools/`),
    ])
    toolsByIntegration.value[integrationUuid] = builtIn
    customToolsByIntegration.value[integrationUuid] = custom
  }
  catch {
    // silently fail
  }
  finally {
    toolsLoading.value[integrationUuid] = false
  }
}

onMounted(async () => {
  await Promise.all([
    appIntegrationStore.load(props.applicationUuid),
    integrationStore.load(),
  ])
  populateFromExisting()

  for (const type of SUPPORTED_INTEGRATION_TYPES) {
    const existing = getExistingIntegration(type.id)
    if (existing) {
      loadToolsForIntegration(existing.uuid)
    }
  }
})

async function save(typeId: IntegrationTypeId) {
  const state = sectionState.value[typeId]
  sectionErrors.value[typeId] = null
  state.saving = true

  const { handleError, apiError } = useApiErrorHandling()

  try {
    await appIntegrationStore.create(props.applicationUuid, {
      integration_uuid: state.integrationUuid,
      integration_type: typeId,
      metadata: { repo: state.repo },
    })
    toast.success('Integration saved')

    const existing = getExistingIntegration(typeId)
    if (existing) {
      loadToolsForIntegration(existing.uuid)
    }
  }
  catch (error: unknown) {
    handleError(error)
    sectionErrors.value[typeId] = apiError.value
  }
  finally {
    state.saving = false
  }
}

async function toggleBuiltInTool(integrationUuid: string, tool: BuiltInTool, newValue: boolean) {
  const previous = tool.is_enabled
  tool.is_enabled = newValue

  try {
    await httpPatch(
      `/applications/${props.applicationUuid}/integrations/${integrationUuid}/tools/${tool.tool_id}/`,
      { is_enabled: newValue },
    )
  }
  catch {
    tool.is_enabled = previous
    toast.error(`Failed to update tool "${tool.title}"`)
  }
}

async function toggleCustomTool(integrationUuid: string, ct: CustomTool, newValue: boolean) {
  const previous = ct.is_enabled
  ct.is_enabled = newValue

  try {
    await httpPatch(
      `/applications/${props.applicationUuid}/integrations/${integrationUuid}/custom-tools/${ct.uuid}/`,
      { is_enabled: newValue },
    )
  }
  catch {
    ct.is_enabled = previous
    toast.error(`Failed to update custom tool "${ct.title}"`)
  }
}

function resetCustomToolForm() {
  customToolForm.value.title = ''
  customToolForm.value.description = ''
  customToolForm.value.urlSchema = ''
  customToolForm.value.editingUuid = null
  customToolForm.value.error = ''
  customToolForm.value.fieldErrors = { title: '', description: '', urlSchema: '' }
}

function openAddCustomTool(integrationUuid: string) {
  resetCustomToolForm()
  customToolForm.value.integrationUuid = integrationUuid
  slideOverOpen.value = true
}

function openEditCustomTool(integrationUuid: string, ct: CustomTool) {
  resetCustomToolForm()
  customToolForm.value.integrationUuid = integrationUuid
  customToolForm.value.editingUuid = ct.uuid
  customToolForm.value.title = ct.title
  customToolForm.value.description = ct.description
  customToolForm.value.urlSchema = ct.url_schema
  slideOverOpen.value = true
}

function validateCustomToolForm(): boolean {
  let valid = true
  const fe = customToolForm.value.fieldErrors
  fe.title = ''
  fe.description = ''
  fe.urlSchema = ''

  if (!customToolForm.value.title.trim()) {
    fe.title = 'Title is required'
    valid = false
  }
  if (!customToolForm.value.description.trim()) {
    fe.description = 'Description is required'
    valid = false
  }
  if (!customToolForm.value.urlSchema.trim()) {
    fe.urlSchema = 'URL Schema is required'
    valid = false
  }
  return valid
}

async function submitCustomTool() {
  if (!validateCustomToolForm()) return

  customToolForm.value.saving = true
  customToolForm.value.error = ''

  const { integrationUuid, editingUuid, title, description, urlSchema } = customToolForm.value
  const payload = { title: title.trim(), description: description.trim(), url_schema: urlSchema.trim() }

  try {
    if (editingUuid) {
      const updated = await httpPatch<CustomTool>(
        `/applications/${props.applicationUuid}/integrations/${integrationUuid}/custom-tools/${editingUuid}/`,
        payload,
      )
      const list = customToolsByIntegration.value[integrationUuid] ?? []
      const idx = list.findIndex(ct => ct.uuid === editingUuid)
      if (idx !== -1) list[idx] = updated
      toast.success('Custom tool updated')
    }
    else {
      const created = await httpPost<CustomTool>(
        `/applications/${props.applicationUuid}/integrations/${integrationUuid}/custom-tools/`,
        payload,
      )
      if (!customToolsByIntegration.value[integrationUuid]) {
        customToolsByIntegration.value[integrationUuid] = []
      }
      customToolsByIntegration.value[integrationUuid].push(created)
      toast.success('Custom tool added')
    }
    slideOverOpen.value = false
  }
  catch (err: unknown) {
    const e = err as { message?: string }
    customToolForm.value.error = e?.message ?? 'An error occurred. Please try again.'
  }
  finally {
    customToolForm.value.saving = false
  }
}

function openDeleteConfirm(integrationUuid: string, ct: CustomTool) {
  deleteConfirm.value.integrationUuid = integrationUuid
  deleteConfirm.value.toolUuid = ct.uuid
  deleteConfirm.value.open = true
}

async function confirmDelete() {
  const { integrationUuid, toolUuid } = deleteConfirm.value
  try {
    await httpDelete(`/applications/${props.applicationUuid}/integrations/${integrationUuid}/custom-tools/${toolUuid}/`)
    customToolsByIntegration.value[integrationUuid] = (
      customToolsByIntegration.value[integrationUuid] ?? []
    ).filter(ct => ct.uuid !== toolUuid)
    toast.success('Custom tool deleted')
  }
  catch {
    toast.error('Failed to delete custom tool')
  }
  finally {
    deleteConfirm.value.open = false
  }
}
</script>
