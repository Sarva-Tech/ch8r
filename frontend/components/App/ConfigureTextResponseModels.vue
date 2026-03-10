<template>
  <ConfigureAIModels :config="textResponseConfig" />
</template>

<script setup lang="ts">
import ConfigureAIModels from './ConfigureAIModels.vue'

const textResponseConfig = {
  title: 'Response Model',
  description: 'Configure AI model to generate text responses.',
  modelLabel: 'Response Model',
  modelPlaceholder: 'Select response models',
  capability: 'text',
  context: 'response',
  successMessage: 'Text response models configured successfully',
}
</script>
