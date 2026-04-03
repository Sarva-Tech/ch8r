<template>
  <div
    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
    :class="statusClasses"
  >
    <div
      class="w-2 h-2 rounded-full mr-1"
      :class="dotClasses"
    />
    {{ statusLabel }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const statusConfig = {
  pending: {
    label: 'Pending',
    color: 'gray'
  },
  extracting: {
    label: 'Extracting',
    color: 'blue'
  },
  processing: {
    label: 'Processing',
    color: 'blue'
  },
  processed: {
    label: 'Processed',
    color: 'green'
  },
  completed: {
    label: 'Completed',
    color: 'green'
  },
  failed: {
    label: 'Failed',
    color: 'red'
  },
  duplicate: {
    label: 'Duplicate',
    color: 'yellow'
  },
  reprocessing: {
    label: 'Reprocessing',
    color: 'blue'
  }
}

const statusLabel = computed(() => {
  return statusConfig[props.status as keyof typeof statusConfig]?.label || props.status
})

const statusColor = computed(() => {
  return statusConfig[props.status as keyof typeof statusConfig]?.color || 'gray'
})

const statusClasses = computed(() => {
  const color = statusColor.value
  const colorClasses = {
    gray: 'bg-gray-100 text-gray-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800'
  }
  return colorClasses[color as keyof typeof colorClasses] || colorClasses.gray
})

const dotClasses = computed(() => {
  const color = statusColor.value
  const dotColorClasses = {
    gray: 'bg-gray-400',
    blue: 'bg-blue-400',
    green: 'bg-green-400',
    red: 'bg-red-400',
    yellow: 'bg-yellow-400'
  }
  return dotColorClasses[color as keyof typeof dotColorClasses] || dotColorClasses.gray
})
</script>
