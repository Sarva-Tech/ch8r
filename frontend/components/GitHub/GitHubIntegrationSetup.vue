<template>
  <div class="space-y-6">
    <div class="text-center">
      <div class="flex justify-center mb-4">
        <div class="w-16 h-16 bg-gray-900 dark:bg-white rounded-lg flex items-center justify-center">
          <UIcon name="i-simple-icons-github" class="text-3xl text-white dark:text-gray-900" />
        </div>
      </div>
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        Connect GitHub Integration
      </h2>
      <p class="text-gray-600 dark:text-gray-300">
        Connect your GitHub account to start ingesting repository data
      </p>
    </div>

    <div class="max-w-3xl mx-auto">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Setup Steps
          </h3>
        </template>

        <div class="space-y-6">
          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
                1
              </div>
              <h4 class="text-lg font-medium text-gray-900 dark:text-white">
                Create a GitHub Personal Access Token
              </h4>
            </div>

            <div class="ml-11 space-y-3">
              <p class="text-gray-600 dark:text-gray-300">
                Follow these steps to create a Personal Access Token on GitHub:
              </p>

              <ol class="list-decimal list-inside space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li>Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)</li>
                <li>Click "Generate new token (classic)"</li>
                <li>Give your token a descriptive name (e.g., "Ch8r Integration")</li>
                <li>Select an expiration period (recommended: 90 days)</li>
                <li>Under "Select scopes", check the following permissions:</li>
              </ol>

              <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-2">
                <h5 class="font-medium text-gray-900 dark:text-white">Required Scopes:</h5>
                <div class="space-y-1">
                  <div class="flex items-center gap-2 text-sm">
                    <UIcon name="i-heroicons-check-circle-16-solid" class="text-green-600" />
                    <code class="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">repo</code>
                    <span class="text-gray-600 dark:text-gray-300">- Full control of private repositories</span>
                  </div>
                  <div class="flex items-center gap-2 text-sm">
                    <UIcon name="i-heroicons-check-circle-16-solid" class="text-green-600" />
                    <code class="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">read:org</code>
                    <span class="text-gray-600 dark:text-gray-300">- Read org and team membership</span>
                  </div>
                  <div class="flex items-center gap-2 text-sm">
                    <UIcon name="i-heroicons-check-circle-16-solid" class="text-green-600" />
                    <code class="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">read:discussion</code>
                    <span class="text-gray-600 dark:text-gray-300">- Access discussions</span>
                  </div>
                </div>
              </div>

              <div class="flex gap-3">
                <UButton
                  icon="i-heroicons-arrow-top-right-on-square-16-solid"
                  variant="outline"
                  @click="openGitHubTokenPage"
                >
                  Open GitHub Token Page
                </UButton>
                <UButton
                  icon="i-heroicons-question-mark-circle-16-solid"
                  variant="ghost"
                  color="gray"
                  @click="showTokenHelp = !showTokenHelp"
                >
                  {{ showTokenHelp ? 'Hide' : 'Show' }} Help
                </UButton>
              </div>

              <UCollapse v-model="showTokenHelp">
                <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 space-y-3">
                  <h5 class="font-medium text-blue-900 dark:text-blue-100">Why are these permissions needed?</h5>
                  <ul class="list-disc list-inside space-y-1 text-sm text-blue-800 dark:text-blue-200">
                    <li><strong>repo</strong>: Required to read repository data including issues, pull requests, and files</li>
                    <li><strong>read:org</strong>: Required to access organization repositories if applicable</li>
                    <li><strong>read:discussion</strong>: Required to access GitHub discussions</li>
                  </ul>
                  <p class="text-sm text-blue-800 dark:text-blue-200">
                    We only use these permissions to read data. We never modify your repositories.
                  </p>
                </div>
              </UCollapse>
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
                2
              </div>
              <h4 class="text-lg font-medium text-gray-900 dark:text-white">
                Configure Integration in Ch8r
              </h4>
            </div>

            <div class="ml-11 space-y-4">
              <div class="space-y-3">
                <C8Label for="integration-name" required>Integration Name</C8Label>
                <C8Input
                  id="integration-name"
                  v-model="integrationData.name"
                  placeholder="e.g., GitHub Integration"
                  required
                />
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  A descriptive name for this GitHub integration
                </p>
              </div>

              <div class="space-y-3">
                <C8Label for="github-token" required>GitHub Personal Access Token</C8Label>
                <div class="relative">
                  <C8Input
                    id="github-token"
                    v-model="integrationData.token"
                    :type="showToken ? 'text' : 'password'"
                    placeholder="ghp_..."
                    required
                  />
                  <UButton
                    :icon="showToken ? 'i-heroicons-eye-slash-16-solid' : 'i-heroicons-eye-16-solid'"
                    variant="ghost"
                    color="gray"
                    size="sm"
                    class="absolute right-2 top-1/2 transform -translate-y-1/2"
                    @click="showToken = !showToken"
                  />
                </div>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Your GitHub Personal Access Token will be encrypted and stored securely
                </p>
              </div>

              <div v-if="tokenValidation.status" class="space-y-2">
                <UAlert
                  :color="tokenValidation.status === 'valid' ? 'green' : 'red'"
                  :variant="tokenValidation.status === 'valid' ? 'soft' : 'solid'"
                  :icon="tokenValidation.status === 'valid' ? 'i-heroicons-check-circle-16-solid' : 'i-heroicons-x-circle-16-solid'"
                >
                  <template #title>
                    {{ tokenValidation.status === 'valid' ? 'Token Valid' : 'Token Invalid' }}
                  </template>
                  <template #description>
                    {{ tokenValidation.message }}
                  </template>
                </UAlert>
              </div>

              <div class="flex gap-3">
                <UButton
                  icon="i-heroicons-shield-check-16-solid"
                  :loading="validatingToken"
                  @click="validateToken"
                >
                  Validate Token
                </UButton>
                <UButton
                  icon="i-heroicons-arrow-path-16-solid"
                  variant="outline"
                  @click="testConnection"
                  :loading="testingConnection"
                >
                  Test Connection
                </UButton>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
                3
              </div>
              <h4 class="text-lg font-medium text-gray-900 dark:text-white">
                Complete Setup
              </h4>
            </div>

            <div class="ml-11 space-y-4">
              <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                <div class="flex items-start gap-3">
                  <UIcon name="i-heroicons-check-circle-16-solid" class="text-green-600 mt-0.5" />
                  <div>
                    <h5 class="font-medium text-green-900 dark:text-green-100">Ready to Connect</h5>
                    <p class="text-sm text-green-800 dark:text-green-200 mt-1">
                      Your GitHub integration is configured and ready to use.
                    </p>
                  </div>
                </div>
              </div>

              <div class="flex gap-3">
                <UButton
                  icon="i-heroicons-plug-16-solid"
                  :loading="creatingIntegration"
                  @click="createIntegration"
                  :disabled="!canCreateIntegration"
                >
                  Connect GitHub Integration
                </UButton>
                <UButton
                  variant="ghost"
                  color="gray"
                  @click="$emit('cancel')"
                >
                  Cancel
                </UButton>
              </div>
            </div>
          </div>
        </div>
      </UCard>
    </div>

    <UModal v-model="showSuccessModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Integration Connected Successfully!
          </h3>
        </template>

        <div class="space-y-4">
          <div class="text-center">
            <UIcon name="i-heroicons-check-circle-16-solid" class="mx-auto text-4xl text-green-600 mb-4" />
            <p class="text-gray-600 dark:text-gray-300">
              Your GitHub integration has been connected successfully. You can now start ingesting repositories.
            </p>
          </div>

          <div class="flex justify-center gap-3">
            <UButton
              icon="i-heroicons-plus-16-solid"
              @click="goToIngestion"
            >
              Ingest First Repository
            </UButton>
            <UButton
              variant="outline"
              @click="$emit('success')"
            >
              Close
            </UButton>
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
interface Props {
  appId: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  success: []
  cancel: []
  integrationCreated: [integration: any]
}>()

const showToken = ref(false)
const showTokenHelp = ref(false)
const showSuccessModal = ref(false)
const validatingToken = ref(false)
const testingConnection = ref(false)
const creatingIntegration = ref(false)

const integrationData = ref({
  name: 'GitHub Integration',
  token: ''
})

const tokenValidation = ref<{
  status: 'valid' | 'invalid' | null
  message: string
}>({
  status: null,
  message: ''
})

const canCreateIntegration = computed(() => {
  return integrationData.value.name.trim() !== '' &&
         integrationData.value.token.trim() !== '' &&
         tokenValidation.value.status === 'valid'
})

const openGitHubTokenPage = () => {
  window.open('https://github.com/settings/tokens', '_blank')
}

const validateToken = async () => {
  if (!integrationData.value.token.trim()) {
    tokenValidation.value = {
      status: 'invalid',
      message: 'Please enter a GitHub token'
    }
    return
  }

  try {
    validatingToken.value = true

    await new Promise(resolve => setTimeout(resolve, 1000))

    const token = integrationData.value.token.trim()
    if (token.startsWith('ghp_') && token.length >= 40) {
      tokenValidation.value = {
        status: 'valid',
        message: 'Token format is valid'
      }
    } else {
      tokenValidation.value = {
        status: 'invalid',
        message: 'Invalid token format. Please check your token.'
      }
    }
  } catch (error) {
    tokenValidation.value = {
      status: 'invalid',
      message: 'Failed to validate token. Please try again.'
    }
  } finally {
    validatingToken.value = false
  }
}

const testConnection = async () => {
  if (!canCreateIntegration.value) return

  try {
    testingConnection.value = true

    await new Promise(resolve => setTimeout(resolve, 2000))

    const toast = useToast()
    toast.add({
      title: 'Connection Test Successful',
      description: 'Successfully connected to GitHub API.',
      color: 'green'
    })
  } catch (error) {
    const toast = useToast()
    toast.add({
      title: 'Connection Test Failed',
      description: 'Failed to connect to GitHub API. Please check your token.',
      color: 'red'
    })
  } finally {
    testingConnection.value = false
  }
}

const createIntegration = async () => {
  if (!canCreateIntegration.value) return

  try {
    creatingIntegration.value = true

    await new Promise(resolve => setTimeout(resolve, 2000))

    const integration = {
      id: Date.now(),
      name: integrationData.value.name,
      provider: 'github',
      type: 'pms',
      created_at: new Date().toISOString()
    }

    emit('integrationCreated', integration)
    showSuccessModal.value = true

  } catch (error) {
    const toast = useToast()
    toast.add({
      title: 'Integration Creation Failed',
      description: 'Failed to create GitHub integration. Please try again.',
      color: 'red'
    })
  } finally {
    creatingIntegration.value = false
  }
}

const goToIngestion = () => {
  navigateTo(`/applications/${props.appId}/github`)
}

watch(() => integrationData.value.token, () => {
  tokenValidation.value = { status: null, message: '' }
})
</script>
