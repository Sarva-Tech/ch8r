<template>
  <ConfigureAIModels :config="embeddingConfig" />
</template>

<script setup lang="ts">
import ConfigureAIModels from './ConfigureAIModels.vue'

const embeddingConfig = {
  title: 'Embedding Model',
  description: 'Configure AI model to generate embeddings.',
  modelLabel: 'Embedding Model',
  modelPlaceholder: 'Select embedding models',
  capability: 'embedding',
  context: 'response',
  successMessage: 'Embedding models configured successfully',
}
</script>
