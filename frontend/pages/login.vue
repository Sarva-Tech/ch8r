<script setup lang="ts">
import { ref } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import GoogleIcon from '@/components/icons/GoogleIcon.vue'

definePageMeta({
  layout: 'public',
  middleware: ['redirect-if-authenticated'],
})

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)

const token = useCookie('auth_token')
const authUser = useCookie<User>('auth_user')
const userStore = useUserStore()

const config = useRuntimeConfig()
const baseUrl = config.public.apiBaseUrl

const handleLogin = async () => {
  if (loading.value) return
  loading.value = true

  try {
    const response = await $fetch<{ token: string }>(`${baseUrl}/login/`, {
      method: 'POST',
      body: {
        username: email.value,
        password: password.value,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response?.token) {
      toast.error('Invalid credentials')
      return
    }

    token.value = response.token
    toast.success('Login successful!')

    const userResponse = await $fetch<User>(`${baseUrl}/me/`, {
      headers: {
        Authorization: `Token ${token.value}`,
      },
    })

    authUser.value = userResponse
    userStore.setUser(userResponse)

    navigateTo('/')
  } catch (err: any) {
    const message =
      err?.data?.non_field_errors?.[0] ||
      err?.data?.detail ||
      'Login failed. Please try again.'
    toast.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-tr">
    <div class="max-w-md w-full backdrop-blur-md rounded-lg shadow-xl border p-10">
      <header class="mb-8 text-center">
        <h1 class="text-3xl font-extrabold mb-2">Welcome Back!</h1>
        <p class="text-sm">Sign in to continue to your dashboard</p>
      </header>

      <form class="space-y-6" @submit.prevent="handleLogin">
        <div>
          <Label for="email" class="block text-sm font-medium  mb-1">Email</Label>
          <Input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            autofocus
            class="ring-1 ring-gray-300 focus:ring-indigo-500 focus:border-indigo-500 rounded-sm"
          />
        </div>

        <div class="relative">
          <Label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</Label>
          <Input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            required
            placeholder="••••••••"
            class="ring-1  focus:ring-indigo-500 focus:border-indigo-500 rounded-sm pr-10"
            @keyup.enter="handleLogin"
          />
          <button
            type="button"
            class="absolute right-2 top-9 text-gray-500 focus:outline-none"
            aria-label="Toggle password visibility"
            tabindex="-1"
            @click="showPassword = !showPassword"
          >
            <component :is="showPassword ? Eye : EyeOff" class="w-5 h-5" />
          </button>
        </div>

        <Button
          type="submit"
          class="w-full font-semibold text-lg rounded-sm shadow-md transition cursor-pointer"
          :disabled="loading"
        >
          <span v-if="loading">Signing in...</span>
          <span v-else>Sign In</span>
        </Button>


        <Button
          variant="outline"
          class="w-full flex items-center justify-center gap-2 cursor-pointer"
          type="button"
          @click="() => toast.info('Google login not implemented')"
        >
          <GoogleIcon />
          Login with Google
        </Button>

      </form>

      <p class="mt-8 text-center text-sm">
        Don't have an account?
        <a href="/register" class="text-indigo-600 font-semibold hover:underline">Register here</a>
      </p>
    </div>
  </div>
</template>