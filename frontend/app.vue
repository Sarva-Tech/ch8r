<template>
  <Body class="bg-background">
    <NuxtLayout />
  </Body>
</template>

<script setup lang="ts">
const userStore = useUserStore()

useHead({
  script: [
    {
      'src': '/widget.js',
      'defer': true,
      'data-api-base-url': 'http://localhost:8000',
      'data-app-uuid': '2279ab6a-2bd2-4112-ad82-eddbfc561e2b',
      'data-token': 'widget_SHXjQG4WjiY5sco85YlMT_x5mVaXNs5xe3MQ9Zsxg20',
      'data-user-identifier': userStore.getUser.id,
      'data-app-name': 'ch8r support',
      'data-app-description': 'We\'re here to help',
      'data-app-logo-url': 'http://localhost:3000/favicon.ico',
      'data-offset-bottom': '64',
      'data-theme': 'blue',
    }
  ]
})
</script>
