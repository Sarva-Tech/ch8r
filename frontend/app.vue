<template>
  <Body class="bg-background">
    <NuxtLayout />
    <!--    <iframe -->
    <!--      id="ch8r-widget-iframe" -->
    <!--      src="http://localhost:3002/widget.html?token=widget_SHXjQG4WjiY5sco85YlMT_x5mVaXNs5xe3MQ9Zsxg20&app_uuid=2279ab6a-2bd2-4112-ad82-eddbfc561e2b" -->
    <!--      width="88" -->
    <!--      height="88" -->
    <!--      style="border: none; position: fixed; bottom: 20px; right: 20px; z-index: 9999; background: transparent;" -->
    <!--    /> -->
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
      'data-app-name': 'Acme Support',
      'data-app-description': 'We\'re here to help',
      'data-app-logo-url': 'http://localhost:3000/favicon.ico'
    }
  ]
})

onMounted(() => {
  window.addEventListener('message', (event) => {
    if (event.data?.type === 'ch8r-resize') {
      const iframe = document.getElementById('ch8r-widget-iframe')
      if (iframe && event.data.height) {
        iframe.style.height = `${event.data.height}px`
        if (event.data.height > 100) {
          iframe.style.width = '360px'
        } else {
          iframe.style.width = '88px'
        }
      }
    }
  })
})
</script>
