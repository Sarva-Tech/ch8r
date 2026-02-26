<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <h2 class="mt-6 text-3xl font-extrabold text-gray-900">Verifying Email</h2>
        <p class="mt-2 text-sm text-gray-600">
          Please wait while we verify your email...
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

const route = useRoute()
const config = useRuntimeConfig()

onMounted(async () => {
  const token = route.params.token as string

  if (!token) {
    console.error('No token found in verification URL')
    await navigateTo('/login?error=invalid_verification_link')
    return
  }

  try {
    const response = await fetch(`${config.public.apiBaseUrl}/verify-email/${token}/`, {
      method: 'GET',
      redirect: 'manual'
    })

    if (response.status === 302 || response.status === 301) {
      const redirectUrl = response.headers.get('location') || ''

      const urlParams = new URLSearchParams(redirectUrl.split('?')[1] || '')
      const authToken = urlParams.get('token')


      if (authToken) {
        await navigateTo(`/login?token=${authToken}`)
      } else {
        await navigateTo('/login?message=email_verified')
      }
    } else {
      const responseText = await response.text()
      console.error('Unexpected response status:', response.status)
      console.error('Response body:', responseText)
      await navigateTo('/login?error=verification_failed')
    }

  } catch (error: any) {
    console.error('Verification error:', error)
    await navigateTo('/login?error=verification_failed')
  }
})
</script>
