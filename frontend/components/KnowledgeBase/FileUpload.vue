<template>
  <div class="space-y-2">
    <div
      class="flex flex-col items-center justify-center px-6 py-10 border-2 border-dashed rounded-md cursor-pointer hover:bg-muted/50"
      @click="fileInput?.click()"
    >
      <Upload class="w-10 h-10 text-muted-foreground" />
      <div class="mt-4 text-sm text-center text-muted-foreground">
        <p>Drag & drop files here or click to browse</p>
        <p class="text-xs mt-1">Supports PDF, DOCX, TXT, and more</p>
      </div>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        multiple
        @change="handleFileChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Upload } from 'lucide-vue-next'
import { ref } from 'vue'

const props = defineProps<{
  modelValue?: File[]
}>()

const emit = defineEmits(['update:modelValue', 'update:files'])

const fileInput = ref<HTMLInputElement | null>(null)
const files = ref<File[]>(props.modelValue || [])

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    const newFiles = Array.from(input.files)
    files.value = [...files.value, ...newFiles]
    emitFiles()
  }
}

const emitFiles = () => {
  emit('update:modelValue', files.value)
  emit('update:files', files.value)
}

defineExpose({
  clear: () => {
    files.value = []
    emitFiles()
  }
})
</script>