<template>
  <SlideOver
    ref="newIntegrationSlideOver"
    title="Add New Integration"
    :on-submit="handleCreate"
    :loading="isSubmitting"
    :disabled="disabled"
  >
    <template #trigger>
      <Button>Add Integration</Button>
    </template>
    <IntegrationForm />
  </SlideOver>
</template>
<script setup lang="ts">
import { Button } from '~/components/ui/button'
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'

import { computed } from 'vue'
import IntegrationForm from '~/components/Integration/IntegrationForm.vue'

const newIntegrationSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const integrationStore = useIntegrationStore()

const { isSubmitting, meta, validate } = integrationStore.getFormInstance()

onMounted(() => {
  validate()
})

async function handleCreate() {
  try {
    await integrationStore.create()
    newIntegrationSlideOver.value?.closeSlide()
    toast.success('Integration created')
  } catch (e: unknown) {
    integrationStore.setBackendErrors(e.errors)
  }
}

const disabled = computed(() =>
  !meta.value.valid
)
</script>
