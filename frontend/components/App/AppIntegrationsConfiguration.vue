<template>
  <div class="space-y-4">
    <div class="flex justify-end">
      <ConnectIntegration />
    </div>
    <ConfigureIntegration
      v-for="type in INTEGRATION_TYPES"
      :key="type.id"
      :config="type"
    />
  </div>
</template>

<script setup lang="ts">
import ConfigureIntegration from './ConfigureIntegration.vue'
import ConnectIntegration from '~/components/Integration/ConnectIntegration.vue'

const INTEGRATION_TYPES = [
  {
    id: 'version_control',
    title: 'Version Control',
    description: 'Select the version control integration and repository to connect.',
    requiresRepo: true,
    successMessage: 'Version control integration configured',
  },
  {
    id: 'project_management',
    title: 'Project Management',
    description: 'Select the project management integration to connect.',
    requiresRepo: true,
    successMessage: 'Project management integration configured',
  },
]
</script>
