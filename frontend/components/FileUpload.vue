<template>
  <div class="space-y-4">
    <div
      class="flex flex-col items-center justify-center border-2 border-dashed border-muted rounded-2xl p-8 transition-colors duration-300 cursor-pointer bg-muted/20 hover:bg-muted/30"
      :class="{ 'border-primary': isDragging }"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      @click="triggerFileSelect"
    >
      <CloudUpload class="w-8 h-8 text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">Click or drag & drop files ({{ SUPPORTED_FILE_EXTENSIONS_STR }})</p>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        multiple
        accept=".pdf,image/*"
        @change="onFileChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CloudUpload } from 'lucide-vue-next'
import { SUPPORTED_FILE_EXTENSIONS, SUPPORTED_FILE_EXTENSIONS_STR } from '~/lib/consts'

const emit = defineEmits<{
  (e: 'update:files', value: File[]): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const files = ref<File[]>([])
const isDragging = ref(false)

const triggerFileSelect = () => {
  fileInput.value?.click()
}

const onFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    addFiles(Array.from(input.files))
    input.value = ''
  }
}

const onDragOver = () => {
  isDragging.value = true
}

const onDragLeave = () => {
  isDragging.value = false
}

const onDrop = (event: DragEvent) => {
  isDragging.value = false
  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files))
  }
}

const addFiles = (incoming: File[]) => {
  const allowedTypes = SUPPORTED_FILE_EXTENSIONS.map(ext => ext.mime)
  const validFiles = incoming.filter((file) => allowedTypes.includes(file.type))
  files.value.push(...validFiles)
  emit('update:files', files.value)
}
</script>
