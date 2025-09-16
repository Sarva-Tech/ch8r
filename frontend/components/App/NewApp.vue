<script setup lang="ts">
import SlideOver from '~/components/SlideOver.vue'
import { computed, ref } from 'vue'
import { toast } from 'vue-sonner'
import { Input } from '~/components/ui/input'
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

const { handleSubmit, resetForm, validate, isSubmitting, meta } = applicationsStore.initForm()

onMounted(() => {
  validate()
})

const onSubmit = handleSubmit(async (values) => {
  try {
    const newApp = await applicationsStore.createApplicationWithKB(values)
    if (newApp) {
      await selectAppAndNavigate(newApp)
      toast.success(`Application ${newApp.name} created`)
      kbDraft.clear()
      resetForm()
      slideRef.value?.closeSlide()
      emit('success', newApp)
    } else {
      toast.error('Error creating application')
    }
  } catch (e: unknown) {
    applicationsStore.setBackendErrors(e.errors)
    toast.error('Error creating application')
  }
})

defineExpose({
  openSlide: () => slideRef.value?.openSlide(),
})

const slideRef = ref<InstanceType<typeof SlideOver> | null>(null)
const emit = defineEmits(['success'])

const disabled = computed(() =>
  !meta.value.valid
)
</script>

<template>
  <SlideOver
    ref="slideRef"
    title="Create Application"
    submit-text="Create"
    cancel-text="Cancel"
    :on-submit="onSubmit"
    :loading="isSubmitting"
    :disabled="disabled"
  >
    <form class="space-y-4">
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

      <div class="space-y-4">
        <SourceSelector v-model="selectedSourceValue" :sources="sources" />
        <div class="space-y-2">
          <div v-if="isFile" class="space-y-2">
            <Label class="text-sm font-medium">
              Upload Files
            </Label>
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
