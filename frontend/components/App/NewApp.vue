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
import { z } from 'zod'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { setBackendErrors } from '~/lib/utils'

const kbDraft = useKBDraftStore()
const applicationsStore = useApplicationsStore()
const { selectAppAndNavigate } = useNavigation()

const sources = KB_SOURCES
const selectedSourceValue = ref('file')

const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: { name: '' },
})

const { resetForm, isSubmitting, meta } = form

const createNewApp = form.handleSubmit(async (values) => {
  try {
    const newApp = await applicationsStore.createApplicationWithKB(values)
    if (newApp) {
      await selectAppAndNavigate(newApp)
      toast.success(`Application ${newApp.name} created`)
      kbDraft.clear()
      resetForm()
      newAppSlideOver.value?.closeSlide()
      emit('success', newApp)
    } else {
      toast.error('Error creating application')
    }
  } catch (e: unknown) {
    setBackendErrors(form, e.errors)
    toast.error('Error creating application')
  }
})

defineExpose({
  openSlide: () => newAppSlideOver.value?.openSlide(),
})

const newAppSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)
const emit = defineEmits(['success'])

const disabled = computed(() =>
  !meta.value.valid
)
</script>

<template>
  <SlideOver
    ref="newAppSlideOver"
    title="Create Application"
  >
    <form class="space-y-4" @submit.prevent="createNewApp">
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

    <template #submitBtn>
      <C8Button
        label="Create"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="createNewApp"
      />
    </template>
  </SlideOver>
</template>
