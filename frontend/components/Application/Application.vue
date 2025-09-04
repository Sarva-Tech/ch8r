<script setup lang="ts">
import SlideOver from '~/components/SlideOver.vue'
import { ref } from 'vue'
import { toast } from 'vue-sonner'
import { Input } from '@/components/ui/input'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
  FormField,
} from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import SourceSelector from '~/components/KnowledgeBase/SourceSelector.vue'
import FileUpload from '~/components/FileUpload.vue'
import UrlInput from '~/components/KnowledgeBase/UrlInput.vue'
import TextInput from '~/components/KnowledgeBase/TextInput.vue'
import Draft from '~/components/KnowledgeBase/Draft.vue'
import { useKBDraftStore } from '~/stores/kbDraft'
import { KB_SOURCES } from '~/lib/consts'
import { useApplicationsStore } from '~/stores/applications'
import { useNavigation } from '~/composables/useNavigation'

const kbDraft = useKBDraftStore()
const applicationsStore = useApplicationsStore()
const { selectAppAndNavigate } = useNavigation()

const sources = KB_SOURCES
const selectedSourceValue = ref('file')

const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')

const form = applicationsStore.initForm()
const { handleSubmit, resetForm, isSubmitting } = form

const onSubmit = handleSubmit(async (values) => {
  try {
    const newApp = await applicationsStore.createApplicationWithKB(values)
    if (newApp) {
      await selectAppAndNavigate(newApp)
      toast.success(`Application "${newApp.name}" created successfully`)
      kbDraft.clear()
      resetForm()
      emit('success', newApp)
    } else {
      toast.error(applicationsStore.setBackendErrors || 'Failed to create application')
    }
  } catch (err: any) {
    toast.error(err.message || 'Something went wrong')
    console.error('Failed to create application:', err)
  }
})

defineExpose({
  openSlide: () => slideRef.value?.openSlide(),
})

const slideRef = ref<InstanceType<typeof SlideOver> | null>(null)
const emit = defineEmits(['success'])
</script>

<template>
  <SlideOver
    ref="slideRef"
    title="Create Application"
    submit-text="Create"
    cancel-text="Cancel"
    :on-submit="onSubmit"
    :loading="isSubmitting"
  >
    <form class="space-y-4" @submit.prevent="onSubmit">
      <FormField v-slot="{ componentField }" name="name">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Application name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input v-bind="componentField" placeholder="Application name" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <div class="space-y-4 mt-4">
        <SourceSelector v-model="selectedSourceValue" :sources="sources" />
        <div class="space-y-2">
          <div v-if="isFile" class="space-y-2">
            <label for="upload_files" class="text-sm font-medium">
              Upload Files
            </label>
            <FileUpload @update:files="kbDraft.setFiles" />
          </div>
          <UrlInput v-if="isUrl" />
          <TextInput v-if="isText" />
        </div>

        <div class="space-y-2">
          <Draft
            v-for="item in kbDraft.items"
            :key="item.id"
            :item="item"
            @remove="kbDraft.remove"
          />
        </div>
      </div>
    </form>
  </SlideOver>
</template>
