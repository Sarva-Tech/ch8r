<script setup lang="ts">
import { ref } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

definePageMeta({
  layout: 'public',
  middleware: ['redirect-if-authenticated'],
})

const email = ref('')
const password = ref('')
const showPassword = ref(false)

const token = useCookie('auth_token')
const authUser = useCookie<User>('auth_user')
const userStore = useUserStore()

const baseUrl = 'http://localhost:8000/api'

const handleLogin = async () => {
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
  } catch (err) {
    toast.error('Login failed. Please try again.')
    console.error('Login error:', err)
  }
}
</script>

<template>
  <div
    class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-tr from-indigo-100 via-white to-pink-100 px-6"
  >
    <div
      class="max-w-md w-full bg-white/90 backdrop-blur-md rounded-lg shadow-xl border border-gray-200 p-10"
    >
      <header class="mb-8 text-center">
        <h1 class="text-3xl font-extrabold text-indigo-700 mb-2">Welcome Back!</h1>
        <p class="text-gray-600 text-sm">Sign in to continue to your dashboard</p>
      </header>

      <form class="space-y-6" @submit.prevent="handleLogin">
        <div>
          <Label for="email" class="block text-sm font-medium text-gray-700 mb-1"
          >Email</Label
          >
          <Input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            class="ring-1 ring-gray-300 focus:ring-indigo-500 focus:border-indigo-500 rounded-sm"
          />
        </div>

        <div class="relative">
          <Label for="password" class="block text-sm font-medium text-gray-700 mb-1"
          >Password</Label
          >
          <Input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            required
            placeholder="••••••••"
            class="ring-1 ring-gray-300 focus:ring-indigo-500 focus:border-indigo-500 rounded-sm pr-10"
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
          class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-lg rounded-sm shadow-md transition"
        >
          Sign In
        </Button>
        <Button
          variant="outline"
          class="w-full flex items-center justify-center gap-2"
          type="button"
          @click="() => toast.info('Google login not implemented')"
        >
          <svg
            class="w-5 h-5"
            viewBox="0 0 533.5 544.3"
            xmlns="http://www.w3.org/2000/svg"
            fill="currentColor"
          >
            <path
              d="M533.5 278.4c0-17.4-1.6-34.1-4.6-50.4H272v95.4h147.4c-6.3 33.9-25.7 62.6-54.8 81.8v68.2h88.7c51.9-47.8 81.2-118 81.2-194.9z"
              fill="#4285f4"
            />
            <path
              d="M272 544.3c73.4 0 134.9-24.3 179.9-66.2l-88.7-68.2c-24.7 16.6-56.3 26.3-91.2 26.3-69.9 0-129.3-47.1-150.6-110.3H32.4v69.3C77.5 484.7 167.2 544.3 272 544.3z"
              fill="#34a853"
            />
            <path
              d="M121.4 321.9c-5.9-17.4-9.3-36-9.3-55s3.4-37.6 9.3-55V142.1H32.4c-19.1 38.4-30 81.6-30 126.9s10.9 88.5 30 126.9l88.9-69z"
              fill="#fbbc04"
            />
            <path
              d="M272 107.7c39.7 0 75.3 13.7 103.4 40.7l77.6-77.6C404.3 24.4 345.8 0 272 0 167.2 0 77.5 59.6 32.4 142.1l88.9 69c21.3-63.2 80.7-110.3 150.7-110.3z"
              fill="#ea4335"
            />
          </svg>
          Login with Google
        </Button>

      </form>

      <p class="mt-8 text-center text-gray-600 text-sm">
        Don't have an account?
        <a href="/register" class="text-indigo-600 font-semibold hover:underline"
        >Register here</a
        >
      </p>
    </div>
  </div>
</template>
