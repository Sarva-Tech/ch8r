<script setup lang="ts">
const appStore = useApplicationsStore()
const route = useRoute()

const { selectAppAndNavigate } = useNavigation()

onMounted(async () => {
  await appStore.fetchApplications()
  const apps = appStore.applications

  if (route.path === '/') {
    const selectedApp: Application = apps[0]
    await selectAppAndNavigate(selectedApp)
  }
})
</script>
<template><div> Loading... </div></template>
