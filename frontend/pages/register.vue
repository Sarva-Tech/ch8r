<script setup lang="ts">
import { ref, watch } from 'vue'
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
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isSubmitting = ref(false)

const baseUrl = 'http://localhost:8000/api'

const passwordsMatch = ref(true)

watch([password, confirmPassword], () => {
  passwordsMatch.value = password.value === confirmPassword.value
})

const handleRegister = async () => {
  if (!passwordsMatch.value) {
    toast.error('Passwords do not match')
    return
  }
  isSubmitting.value = true

  try {
   await $fetch(`${baseUrl}/register/`, {
      method: 'POST',
      body: {
        email: email.value,
        password: password.value,
        username: email.value,
      },
      headers: { 'Content-Type': 'application/json' },
    })
    toast.success('Registration successful! Please login.')
    navigateTo('/login')
  } catch (err: never) {
    const errors = err?.data
    if (errors && typeof errors === 'object') {
      Object.entries(errors).forEach(([, messages]) => {
        if (Array.isArray(messages)) {
          messages.forEach((message) => toast.error(message))
        } else if (typeof messages === 'string') {
          toast.error(messages)
        }
      })
    } else {
      toast.error('Registration failed. Please try again.')
    }

    console.error('Register error:', err)
  } finally {
    isSubmitting.value = false
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
        <h1 class="text-3xl font-extrabold text-indigo-700 mb-2">
          Create Account
        </h1>
        <p class="text-gray-600 text-sm">Fill the form below to register</p>
      </header>

      <form class="space-y-6" novalidate @submit.prevent="handleRegister">
        <div>
          <Label
            for="email"
            class="block text-sm font-medium text-gray-700 mb-1"
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
          <Label
            for="password"
            class="block text-sm font-medium text-gray-700 mb-1"
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

        <div class="relative">
          <Label
            for="confirmPassword"
            class="block text-sm font-medium text-gray-700 mb-1"
            >Confirm Password</Label
          >
          <Input
            id="confirmPassword"
            v-model="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            required
            placeholder="••••••••"
            :class="[
              'ring-1 focus:ring-indigo-500 focus:border-indigo-500 rounded-sm pr-10',
              passwordsMatch ? 'ring-gray-300' : 'ring-red-500',
            ]"
          />
          <button
            type="button"
            class="absolute right-2 top-9 text-gray-500 focus:outline-none"
            aria-label="Toggle confirm password visibility"
            tabindex="-1"
            @click="showConfirmPassword = !showConfirmPassword"
          >
            <component
              :is="showConfirmPassword ? Eye : EyeOff"
              class="w-5 h-5"
            />
          </button>
          <p v-if="!passwordsMatch" class="text-sm text-red-600 mt-1">
            Passwords do not match
          </p>
        </div>

        <Button
          type="submit"
          class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-lg rounded-sm shadow-md transition"
          :disabled="isSubmitting"
        >
          Register
        </Button>
      </form>

      <p class="mt-8 text-center text-gray-600 text-sm">
        Already have an account?
        <a href="/login" class="text-indigo-600 font-semibold hover:underline"
          >Login here</a
        >
      </p>
    </div>
  </div>
</template>
