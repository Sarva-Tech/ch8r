<script setup lang="ts">
const appStore = useApplicationsStore()
const route = useRoute()

const { selectAndNavigate } = useAppNavigation()

onMounted(async () => {
  await appStore.fetchApplications()
  const apps = appStore.applications

  if (route.path === '/') {
    const selectedApp: Application = apps[0]
    await selectAndNavigate(selectedApp)
  }
})
</script>
<template><div> Loading... </div></template>
