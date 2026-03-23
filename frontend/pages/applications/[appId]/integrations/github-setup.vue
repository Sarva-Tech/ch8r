<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="container mx-auto px-4 py-8">
      <GitHubIntegrationSetup
        :app-id="appId"
        @success="handleSuccess"
        @cancel="handleCancel"
        @integration-created="handleIntegrationCreated"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'minimal'
})

const route = useRoute()
const appId = route.params.appId as string

const handleSuccess = () => {
  navigateTo(`/applications/${appId}/integrations`)
}

const handleCancel = () => {
  navigateTo(`/applications/${appId}/integrations`)
}

const handleIntegrationCreated = (integration: any) => {
  const toast = useToast()
  toast.add({
    title: 'GitHub Integration Created',
    description: 'Your GitHub integration has been set up successfully.',
    color: 'green'
  })
}
</script>
