<template>
  <SlideOver
    ref="newModelSlideOver"
    title="Bring Your Own Model"
    :on-submit="handleCreate"
    :loading="isSubmitting"
    :disabled="disabled"
  >
    <template #trigger>
      <Button>Add Model</Button>
    </template>
    <ModelForm />
  </SlideOver>
</template>
<script setup lang="ts">
import { Button } from '~/components/ui/button'
import ModelForm from '~/components/Model/ModelForm.vue'
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'

import { computed } from 'vue'

const newModelSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const modelStore = useModelStore()

const { isSubmitting, meta, validate } = modelStore.getFormInstance()

onMounted(() => {
  validate()
})

async function handleCreate() {
  try {
    await modelStore.create()
    newModelSlideOver.value?.closeSlide()
    toast.success('Model created')
  } catch (e: unknown) {
    modelStore.setBackendErrors(e.errors)
  }
}

const disabled = computed(() =>
  !meta.value.valid
)
</script>
