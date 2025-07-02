<script lang="ts" setup>
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const userStore = useUserStore()

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()

const email = ref('')
const password = ref('')
const baseUrl = 'http://localhost:8000/api'
const token = useCookie('auth_token')

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

    if (response?.token) {
      token.value = response.token
      console.log('Login successful.')

      const userResponse = await $fetch<User>(`${baseUrl}/me/`, {
        headers: {
          Authorization: `Token ${token.value}`,
        },
      })

      userStore.setUser(userResponse)
      navigateTo('/')
    } else {
      console.error('No token returned')
    }
    console.log('Login success:', response)
  } catch (err) {
    console.error('Login failed:', err)
  }
}
</script>

<template>
  <div class="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
    <div class="w-full max-w-sm">
      <div :class="cn('flex flex-col gap-6', props.class)">
        <Card>
          <CardHeader>
            <CardTitle>Login to your account</CardTitle>
            <CardDescription>
              Enter your email below to login to your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form @submit.prevent>
              <div class="flex flex-col gap-6">
                <div class="grid gap-3">
                  <Label for="email">Email</Label>
                  <Input
                    id="email"
                    v-model="email"
                    placeholder="m@example.com"
                    required
                    type="email"
                  />
                </div>
                <div class="grid gap-3">
                  <div class="flex items-center">
                    <Label for="password">Password</Label>
                    <a
                      class="ml-auto inline-block text-sm underline-offset-4 hover:underline"
                      href="#"
                    >
                      Forgot your password?
                    </a>
                  </div>
                  <Input
                    id="password"
                    v-model="password"
                    required
                    type="password"
                  />
                </div>
                <div class="flex flex-col gap-3">
                  <Button class="w-full" type="submit" @click.prevent="handleLogin">
                    Login
                  </Button>
                  <Button class="w-full" variant="outline">
                    Login with Google
                  </Button>
                </div>
              </div>
              <div class="mt-4 text-center text-sm">
                Don't have an account?
                <a class="underline underline-offset-4" href="#"> Sign up </a>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
