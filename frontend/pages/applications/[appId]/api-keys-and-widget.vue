<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import NewApiKey from '~/components/ApiKey/NewApiKey.vue'
import type { APIKeyItem } from '~/stores/apiKey'
import { CircleAlert, Key, Calendar, Shield, Trash, Code2, Copy, Check, ChevronDown, Zap, Settings2, Globe, RefreshCw, Monitor } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import Clipboard from '~/components/Clipboard.vue'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import C8Dialog from '~/components/C8Dialog.vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Label } from '~/components/ui/label'
import { Switch } from '~/components/ui/switch'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'

const enablingWidget = ref(false)
const isDeleteDialogOpen = ref(false)
const apiKeyToDelete = ref<APIKeyItem | null>(null)
const loading = ref(false)
const copiedSnippet = ref<string | null>(null)
const showAdvanced = ref(false)
const previewKey = ref(0) // increment to force iframe reload
const previewIframe = ref<HTMLIFrameElement | null>(null)

// Config builder state
const configTheme = ref('neutral')
const configDarkMode = ref('auto')
const configPosition = ref('bottom-right')
const configAppName = ref('')
const configAppDescription = ref('')
const configAiGreeting = ref('')

const apiKeyStore = useAPIKeyStore()
const widgetStore = useWidgetStore()
const applicationsStore = useApplicationsStore()
const user = useUserStore()

const apiKeys = computed(() => apiKeyStore.apiKeys)
const widget = computed(() => widgetStore.widget)
const newAPIKey = computed(() => apiKeyStore.newAPIKey)
const widgetEnabled = computed(() => ['enabled', 'active'].includes(widget.value?.status || 'disabled'))
const appUuid = computed(() => applicationsStore.selectedApplication?.uuid ?? '')

const runtimeConfig = useRuntimeConfig()

// Live preview srcdoc — loads /widget.js with config injected inline
const previewSrcdoc = computed(() => {
  if (!widget.value || !appUuid.value) return ''
  // Strip trailing /api from the runtime config URL to get the base origin
  const apiBase = (runtimeConfig.public.apiBaseUrl as string).replace(/\/api\/?$/, '')
  const cfg: Record<string, string> = {
    appUuid: appUuid.value,
    token: widget.value.token,
    position: configPosition.value,
    apiBaseUrl: apiBase,
  }
  if (configTheme.value !== 'neutral') cfg.theme = configTheme.value
  if (configDarkMode.value !== 'auto') cfg.darkMode = configDarkMode.value
  if (configAppName.value) cfg.appName = configAppName.value
  if (configAppDescription.value) cfg.appDescription = configAppDescription.value
  if (configAiGreeting.value) cfg.aiGreeting = configAiGreeting.value

  const cfgJson = JSON.stringify(cfg, null, 2)
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { width: 100%; height: 100%; background: #f5f5f5; font-family: system-ui, sans-serif; }
    .preview-bg {
      width: 100%; height: 100%;
      display: flex; align-items: center; justify-content: center;
      background: repeating-linear-gradient(
        45deg,
        transparent, transparent 10px,
        rgba(128,128,128,0.05) 10px, rgba(128,128,128,0.05) 20px
      );
    }
    .preview-label {
      position: absolute; top: 12px; left: 12px;
      font-size: 11px; color: rgba(128,128,128,0.6);
      font-family: system-ui, sans-serif;
      pointer-events: none;
    }
  </style>
</head>
<body>
  <div class="preview-bg">
    <span class="preview-label">Live preview</span>
  </div>
  <script>
    window.Ch8rWidgetConfig = ${cfgJson};
  <\/script>
  <script src="/widget.js"><\/script>
  <script>
    // Auto-open the widget once it's ready, and handle live config updates
    (function () {
      function tryOpen() {
        var root = document.getElementById('ch8r-widget-root');
        if (!root || !root.shadowRoot) { setTimeout(tryOpen, 100); return; }
        // Dispatch a synthetic click on the launcher button to open the widget
        var launcher = root.shadowRoot.querySelector('button');
        if (launcher) { launcher.click(); }
      }
      setTimeout(tryOpen, 300);

      window.addEventListener('message', function (e) {
        if (!e.data || e.data.type !== 'ch8r-preview-update') return;
        var update = e.data.payload;
        var root = document.getElementById('ch8r-widget-root');
        if (!root || !root.shadowRoot) return;

        // Update theme CSS
        if (update.theme !== undefined) {
          var themeStyle = root.shadowRoot.getElementById('ch8r-theme');
          if (themeStyle && window.__ch8rBuildThemeCSS) {
            themeStyle.textContent = window.__ch8rBuildThemeCSS(update.theme);
          }
        }

        // Update dark mode class on shadow host
        if (update.darkMode !== undefined) {
          if (update.darkMode === 'true') {
            root.classList.add('dark');
          } else if (update.darkMode === 'false') {
            root.classList.remove('dark');
          }
          // 'auto' — leave it to the detector already running
        }

        // Update config signal (appName, appDescription, aiGreeting, position, etc.)
        // Assign a new object to trigger Preact signal reactivity
        if (window.__ch8rConfig && update.config) {
          window.__ch8rConfig.value = Object.assign({}, window.__ch8rConfig.value, update.config);
        }
      });
    })();
  <\/script>
</body>
</html>`
})

// All config changes send a live postMessage update; position changes also regenerate srcdoc (iframe reloads)
watch([configTheme, configDarkMode, configAppName, configAppDescription, configAiGreeting], ([theme, darkMode, appName, appDescription, aiGreeting]) => {
  const iframe = previewIframe.value
  if (!iframe?.contentWindow) { previewKey.value++; return }
  iframe.contentWindow.postMessage({
    type: 'ch8r-preview-update',
    payload: {
      theme,
      darkMode,
      config: { appName, appDescription, aiGreeting },
    },
  }, '*')
})

function refreshPreview() {
  previewKey.value++
}

// Build optional data attributes for snippet
const optionalAttrs = computed(() => {
  const attrs: string[] = []
  if (configTheme.value !== 'neutral') attrs.push(`  data-theme="${configTheme.value}"`)
  if (configDarkMode.value !== 'auto') attrs.push(`  data-dark-mode="${configDarkMode.value}"`)
  if (configPosition.value !== 'bottom-right') attrs.push(`  data-position="${configPosition.value}"`)
  if (configAppName.value) attrs.push(`  data-app-name="${configAppName.value}"`)
  if (configAppDescription.value) attrs.push(`  data-app-description="${configAppDescription.value}"`)
  if (configAiGreeting.value) attrs.push(`  data-ai-greeting="${configAiGreeting.value}"`)
  return attrs
})

const scriptSnippet = computed(() => {
  if (!widget.value) return ''
  const base = `<script\n  src="/widget.js"\n  data-app-uuid="${appUuid.value}"\n  data-token="${widget.value.token}"`
  const extras = optionalAttrs.value.length ? '\n' + optionalAttrs.value.join('\n') : ''
  return base + extras + `\n><\/script>`
})

const windowConfigSnippet = computed(() => {
  if (!widget.value) return ''
  const cfg: Record<string, string> = { appUuid: appUuid.value, token: widget.value.token }
  if (configTheme.value !== 'neutral') cfg.theme = configTheme.value
  if (configDarkMode.value !== 'auto') cfg.darkMode = configDarkMode.value
  if (configPosition.value !== 'bottom-right') cfg.position = configPosition.value
  if (configAppName.value) cfg.appName = configAppName.value
  if (configAppDescription.value) cfg.appDescription = configAppDescription.value
  if (configAiGreeting.value) cfg.aiGreeting = configAiGreeting.value
  const entries = Object.entries(cfg).map(([k, v]) => `    ${k}: "${v}"`).join(',\n')
  return `<script>\n  window.Ch8rWidgetConfig = {\n${entries}\n  };\n<\/script>\n<script src="/widget.js"><\/script>`
})

async function copySnippet(key: string, text: string) {
  await navigator.clipboard.writeText(text)
  copiedSnippet.value = key
  setTimeout(() => { copiedSnippet.value = null }, 2000)
}

function deleteAPIKey(apiKey: APIKeyItem) {
  apiKeyStore.delete(apiKey.id).then((response) => {
    if (response?.detail === 'deleted') toast.success('API key deleted')
  }).catch(() => toast.error('Failed to delete API key'))
}

function openDeleteDialog(apiKey: APIKeyItem) {
  apiKeyToDelete.value = apiKey
  isDeleteDialogOpen.value = true
}

function confirmDelete() {
  if (apiKeyToDelete.value) deleteAPIKey(apiKeyToDelete.value)
}

function canManageApiKey(apiKey: APIKeyItem) {
  return user.authUser?.id === apiKey.owner
}

onMounted(async () => {
  loading.value = true
  try { await apiKeyStore.load() } catch { toast.error('Failed to load API keys') }
  try {
    widgetStore.widget = null
    await widgetStore.load()
  } catch { toast.error('Failed to load widget configuration') }
  finally { loading.value = false }
})

async function toggleWidget() {
  enablingWidget.value = true
  try {
    await widgetStore.toggle()
    toast.success(widgetEnabled.value ? 'Widget integration enabled' : 'Widget integration disabled')
  } catch { toast.error('Error configuring widget integration') }
  finally { enablingWidget.value = false }
}
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto space-y-6">

    <!-- API Keys -->
    <div class="w-full space-y-3">
      <div class="flex items-center gap-2 py-2">
        <h2 class="text-lg font-semibold">API Keys</h2>
        <div class="ml-auto"><NewApiKey /></div>
      </div>

      <Alert v-if="newAPIKey" class="py-4">
        <CircleAlert class="h-4 w-4" />
        <AlertTitle>Don't forget to copy your new API Key</AlertTitle>
        <AlertDescription>
          This API Key won't be shown again for your security.
          <div class="relative w-full max-w-sm flex mt-2">
            <Input v-model="newAPIKey.api_key" type="text" disabled class="pr-10" />
            <span class="absolute end-0 inset-y-0 flex items-center justify-center text-muted-foreground hover:text-foreground">
              <Clipboard :text="newAPIKey.api_key" />
            </span>
          </div>
        </AlertDescription>
      </Alert>

      <div v-if="loading" class="text-center py-8 text-muted-foreground text-sm">Loading...</div>
      <div v-if="!loading && apiKeys.length === 0" class="text-center py-8 text-muted-foreground text-sm">No API keys yet.</div>

      <div v-if="!loading && apiKeys.length > 0" class="space-y-2">
        <C8Item v-for="(apiKey, index) in apiKeys" :key="index" :icon="Key" container-class="w-full" item-class="w-full">
          <template #title>{{ apiKey.name }}</template>
          <template #details>
            <ItemDescription>
              <div class="inline-flex space-x-3">
                <div class="flex items-center space-x-1"><Shield class="w-4 h-4" /><div>{{ apiKey.permissions?.map((p: string) => p.toUpperCase()).sort().join(', ') }}</div></div>
                <div class="flex items-center space-x-1"><Calendar class="w-4 h-4" /><div>{{ apiKey.created?.split('T')[0] }}</div></div>
              </div>
            </ItemDescription>
          </template>
          <template #dropdown>
            <DropdownMenuItem :disabled="!canManageApiKey(apiKey)" class="text-destructive" @click="openDeleteDialog(apiKey)">
              <Trash class="h-4 w-4 text-destructive" />Delete
            </DropdownMenuItem>
          </template>
        </C8Item>
      </div>

      <C8Dialog v-model:open="isDeleteDialogOpen" :title="`Delete API Key ${apiKeyToDelete?.name}`" confirm-text="Delete" :destructive="true" @confirm="confirmDelete">
        <template #description>Are you sure you want to delete <span class="font-bold">{{ apiKeyToDelete?.name }}</span>?</template>
      </C8Dialog>
    </div>

    <!-- Widget Integration -->
    <Card class="w-full">
      <CardHeader>
        <div class="flex items-start justify-between gap-4">
          <div>
            <CardTitle class="flex items-center gap-2"><Globe class="w-5 h-5" />Widget Integration</CardTitle>
            <CardDescription class="mt-1">Embed the Ch8r chat widget on any website with a single script tag.</CardDescription>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span class="text-sm text-muted-foreground">{{ widgetEnabled ? 'Enabled' : 'Disabled' }}</span>
            <Switch :model-value="widgetEnabled" :disabled="enablingWidget" @click="toggleWidget" />
          </div>
        </div>
      </CardHeader>

      <CardContent v-if="widget && widgetEnabled" class="space-y-6">

        <!-- Credentials -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div class="rounded-lg border bg-muted/40 px-4 py-3 space-y-1">
            <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide">Widget Token</p>
            <div class="flex items-center justify-between gap-2">
              <code class="text-sm font-mono truncate text-foreground">{{ widget.token }}</code>
              <Clipboard :text="widget.token" />
            </div>
          </div>
          <div class="rounded-lg border bg-muted/40 px-4 py-3 space-y-1">
            <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide">App UUID</p>
            <div class="flex items-center justify-between gap-2">
              <code class="text-sm font-mono truncate text-foreground">{{ appUuid }}</code>
              <Clipboard :text="appUuid" />
            </div>
          </div>
        </div>

        <!-- Two-column: config builder + live preview -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">

          <!-- Config builder -->
          <div class="space-y-3">
            <p class="text-sm font-medium flex items-center gap-1.5"><Settings2 class="w-4 h-4" />Configure</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="space-y-1.5">
                <Label class="text-xs text-muted-foreground">Theme</Label>
                <Select v-model="configTheme">
                  <SelectTrigger class="h-8 text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="t in ['neutral','gray','blue','rose','orange','green','yellow','violet']" :key="t" :value="t">{{ t }}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-1.5">
                <Label class="text-xs text-muted-foreground">Dark Mode</Label>
                <Select v-model="configDarkMode">
                  <SelectTrigger class="h-8 text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">auto (follows page)</SelectItem>
                    <SelectItem value="true">always dark</SelectItem>
                    <SelectItem value="false">always light</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-1.5">
                <Label class="text-xs text-muted-foreground">Position</Label>
                <Select v-model="configPosition">
                  <SelectTrigger class="h-8 text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bottom-right">Bottom right</SelectItem>
                    <SelectItem value="bottom-left">Bottom left</SelectItem>
                    <SelectItem value="top-right">Top right</SelectItem>
                    <SelectItem value="top-left">Top left</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-1.5">
                <Label class="text-xs text-muted-foreground">App Name</Label>
                <Input v-model="configAppName" placeholder="e.g. Support" class="h-8 text-sm" />
              </div>
              <div class="space-y-1.5 sm:col-span-2">
                <Label class="text-xs text-muted-foreground">App Description</Label>
                <Input v-model="configAppDescription" placeholder="e.g. We reply in minutes" class="h-8 text-sm" />
              </div>
              <div class="space-y-1.5 sm:col-span-2">
                <Label class="text-xs text-muted-foreground">AI Greeting</Label>
                <Input v-model="configAiGreeting" placeholder="e.g. Hi! How can I help?" class="h-8 text-sm" />
              </div>
            </div>
          </div>

          <!-- Live preview -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium flex items-center gap-1.5"><Monitor class="w-4 h-4" />Live Preview</p>
              <button class="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors" @click="refreshPreview">
                <RefreshCw class="w-3.5 h-3.5" />Refresh
              </button>
            </div>
            <div class="rounded-lg border overflow-hidden bg-muted/20" style="height: 660px;">
              <iframe
                v-if="previewSrcdoc"
                ref="previewIframe"
                :key="previewKey"
                :srcdoc="previewSrcdoc"
                class="w-full h-full border-0"
                sandbox="allow-scripts allow-same-origin allow-forms"
                title="Widget preview"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-sm text-muted-foreground">
                Loading preview…
              </div>
            </div>
            <p class="text-xs text-muted-foreground">Click the chat icon in the preview to test the widget.</p>
          </div>
        </div>

        <!-- Embed code -->
        <div class="space-y-2">
          <p class="text-sm font-medium">Embed code</p>
          <Tabs default-value="script">
            <TabsList class="h-8">
              <TabsTrigger value="script" class="text-xs gap-1.5">
                <Code2 class="w-3.5 h-3.5" />Script tag
                <Badge variant="secondary" class="text-[10px] px-1 py-0 h-4 ml-0.5">Recommended</Badge>
              </TabsTrigger>
              <TabsTrigger value="window" class="text-xs gap-1.5">
                <Zap class="w-3.5 h-3.5" />window.Ch8rWidgetConfig
              </TabsTrigger>
            </TabsList>

            <TabsContent value="script" class="mt-3 space-y-2">
              <p class="text-xs text-muted-foreground">Add before the closing <code class="bg-muted px-1 rounded">&lt;/body&gt;</code> tag. Only <code class="bg-muted px-1 rounded">data-app-uuid</code> and <code class="bg-muted px-1 rounded">data-token</code> are required.</p>
              <div class="relative group">
                <pre class="rounded-lg border bg-muted p-4 text-xs font-mono overflow-x-auto leading-relaxed whitespace-pre">{{ scriptSnippet }}</pre>
                <button class="absolute top-2 right-2 p-1.5 rounded-md bg-background border opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted" @click="copySnippet('script', scriptSnippet)">
                  <Check v-if="copiedSnippet === 'script'" class="w-3.5 h-3.5 text-green-500" />
                  <Copy v-else class="w-3.5 h-3.5 text-muted-foreground" />
                </button>
              </div>
            </TabsContent>

            <TabsContent value="window" class="mt-3 space-y-2">
              <p class="text-xs text-muted-foreground">Use when you need to set config dynamically (e.g. after login or from a CMS). Place the config block before the widget script.</p>
              <div class="relative group">
                <pre class="rounded-lg border bg-muted p-4 text-xs font-mono overflow-x-auto leading-relaxed whitespace-pre">{{ windowConfigSnippet }}</pre>
                <button class="absolute top-2 right-2 p-1.5 rounded-md bg-background border opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted" @click="copySnippet('window', windowConfigSnippet)">
                  <Check v-if="copiedSnippet === 'window'" class="w-3.5 h-3.5 text-green-500" />
                  <Copy v-else class="w-3.5 h-3.5 text-muted-foreground" />
                </button>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        <!-- Config reference -->
        <details class="group">
          <summary class="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground transition-colors list-none flex items-center gap-1.5 select-none">
            <ChevronDown class="w-4 h-4 transition-transform group-open:rotate-180" />All configuration options
          </summary>
          <div class="mt-3 rounded-lg border overflow-hidden text-xs">
            <table class="w-full">
              <thead class="bg-muted/60">
                <tr>
                  <th class="text-left px-3 py-2 font-medium text-muted-foreground">data-* attribute</th>
                  <th class="text-left px-3 py-2 font-medium text-muted-foreground">Config key</th>
                  <th class="text-left px-3 py-2 font-medium text-muted-foreground">Values</th>
                  <th class="text-left px-3 py-2 font-medium text-muted-foreground">Default</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-border">
                <tr class="bg-muted/30"><td colspan="4" class="px-3 py-1.5 font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">Required</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-app-uuid</td><td class="px-3 py-2 font-mono">appUuid</td><td class="px-3 py-2 text-muted-foreground">string</td><td class="px-3 py-2 text-muted-foreground">—</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-token</td><td class="px-3 py-2 font-mono">token</td><td class="px-3 py-2 text-muted-foreground">string</td><td class="px-3 py-2 text-muted-foreground">—</td></tr>
                <tr class="bg-muted/30"><td colspan="4" class="px-3 py-1.5 font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">Appearance</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-theme</td><td class="px-3 py-2 font-mono">theme</td><td class="px-3 py-2 text-muted-foreground">neutral · gray · blue · rose · orange · green · yellow · violet</td><td class="px-3 py-2 font-mono">neutral</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-dark-mode</td><td class="px-3 py-2 font-mono">darkMode</td><td class="px-3 py-2 text-muted-foreground">auto · true · false</td><td class="px-3 py-2 font-mono">auto</td></tr>
                <tr class="bg-muted/30"><td colspan="4" class="px-3 py-1.5 font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">Position</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-position</td><td class="px-3 py-2 font-mono">position</td><td class="px-3 py-2 text-muted-foreground">bottom-right · bottom-left · top-right · top-left</td><td class="px-3 py-2 font-mono">bottom-right</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-offset-bottom</td><td class="px-3 py-2 font-mono">offsetBottom</td><td class="px-3 py-2 text-muted-foreground">number (px)</td><td class="px-3 py-2 font-mono">16</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-offset-right</td><td class="px-3 py-2 font-mono">offsetRight</td><td class="px-3 py-2 text-muted-foreground">number (px)</td><td class="px-3 py-2 font-mono">16</td></tr>
                <tr class="bg-muted/30"><td colspan="4" class="px-3 py-1.5 font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">Branding</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-app-name</td><td class="px-3 py-2 font-mono">appName</td><td class="px-3 py-2 text-muted-foreground">string</td><td class="px-3 py-2 font-mono">Ch8r</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-app-description</td><td class="px-3 py-2 font-mono">appDescription</td><td class="px-3 py-2 text-muted-foreground">string</td><td class="px-3 py-2 text-muted-foreground">Powered by Ch8r</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-app-logo-url</td><td class="px-3 py-2 font-mono">appLogoUrl</td><td class="px-3 py-2 text-muted-foreground">URL</td><td class="px-3 py-2 text-muted-foreground">—</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-launcher-icon-url</td><td class="px-3 py-2 font-mono">launcherIconUrl</td><td class="px-3 py-2 text-muted-foreground">URL</td><td class="px-3 py-2 text-muted-foreground">—</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-ai-greeting</td><td class="px-3 py-2 font-mono">aiGreeting</td><td class="px-3 py-2 text-muted-foreground">string</td><td class="px-3 py-2 text-muted-foreground">—</td></tr>
                <tr class="bg-muted/30"><td colspan="4" class="px-3 py-1.5 font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">User &amp; API</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-user-identifier</td><td class="px-3 py-2 font-mono">userIdentifier</td><td class="px-3 py-2 text-muted-foreground">string — pre-set user identity</td><td class="px-3 py-2 text-muted-foreground">—</td></tr>
                <tr class="hover:bg-muted/20"><td class="px-3 py-2 font-mono">data-api-base-url</td><td class="px-3 py-2 font-mono">apiBaseUrl</td><td class="px-3 py-2 text-muted-foreground">URL — override API endpoint</td><td class="px-3 py-2 text-muted-foreground">—</td></tr>
              </tbody>
            </table>
          </div>
        </details>

      </CardContent>

      <CardContent v-else-if="!widgetEnabled">
        <div class="flex flex-col items-center justify-center py-8 text-center gap-2">
          <Globe class="w-8 h-8 text-muted-foreground/40" />
          <p class="text-sm text-muted-foreground">Enable widget integration to get your embed code and live preview.</p>
        </div>
      </CardContent>
    </Card>

  </div>
</template>
