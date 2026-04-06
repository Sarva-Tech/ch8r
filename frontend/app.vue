<template>
  <Body class="bg-background">
    <NuxtLayout />
  </Body>
</template>

<script setup lang="ts">
const userStore = useUserStore()
const config = useRuntimeConfig()

useHead({
  script: [
    {
      'src': config.public.widgetUrl,
      'defer': true,
      'data-api-base-url': config.public.widgetApiBaseUrl,
      'data-app-uuid': config.public.widgetAppUuid,
      'data-token': config.public.widgetToken,
      'data-user-identifier': userStore.getUser.id,
      'data-app-name': config.public.widgetAppName,
      'data-app-description': config.public.widgetAppDescription,
      'data-app-logo-url': config.public.widgetAppLogoUrl,
      'data-offset-bottom': config.public.widgetOffsetBottom,
      'data-theme': config.public.widgetTheme,
    }
  ]
})
</script>
