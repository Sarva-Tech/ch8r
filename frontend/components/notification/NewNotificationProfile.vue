<template>
  <SlideOver
    ref="newNotificationSlideOver"
    title="Add Notification Profiles"
    :on-submit="handleCreate"
    :loading="isSubmitting"
    :disabled="disabled"
  >
    <template #trigger>
      <Button>Add Notification Profile</Button>
    </template>
    <NotificationProfileWithDraft ref="notificationForm" />
  </SlideOver>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Button } from '~/components/ui/button'
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import { useNotificationDraftStore } from '~/stores/notificationProfileDraft'

const newNotificationSlideOver = ref<InstanceType<typeof SlideOver> | null>(
  null,
)
const notificationForm = ref<any>(null)

const notificationProfileStore = useNotificationProfileStore()
const draftStore = useNotificationDraftStore()

const { isSubmitting, meta, validate } =
  notificationProfileStore.getFormInstance()

onMounted(() => {
  validate()
})

async function handleCreate() {
  try {
    const bulkProfiles = draftStore.items.map((item) => ({
      name: item.profileName,
      type: item.type,
      config:
        item.type === 'email'
          ? { email: item.value }
          : { webhookUrl: item.value },
    }))

    await notificationProfileStore.createBulkNotificationProfiles(bulkProfiles)
    draftStore.clear()
    newNotificationSlideOver.value?.closeSlide()
    toast.success(`Successfully created notification profiles`)
  } catch (e: any) {
    if (e.errors) {
      notificationProfileStore.setBackendErrors(e.errors)
    } else {
      toast.error(e.message || 'Failed to create notification profiles')
    }
  }
}

const disabled = computed(() => {
  return !(draftStore.hasDrafts || meta.value.valid)
})
</script>