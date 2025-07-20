<script setup>
import Toaster from '@/components/ui/sonner/Sonner.vue'
import 'vue-sonner/style.css'
</script>

<template>
  <div>
    <NuxtPage />
    <ClientOnly>
      <Toaster />
    </ClientOnly>
  </div>
</template>