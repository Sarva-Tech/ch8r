<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Eye, EyeOff, LogIn } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useHttpClient } from '~/composables/useHttpClient'

const config = useRuntimeConfig()

definePageMeta({
  layout: 'public',
  middleware: ['redirect-if-authenticated'],
})

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const openInactiveAccountDialog = ref(false)
const dialogMessage = ref('')
const showResendOption = ref(false)
const userEmail = ref('')
const resendLoading = ref(false)


const handleLogin = async () => {
  if (loading.value) return
  loading.value = true

  const userStore = useUserStore()
  const { httpPost } = useHttpClient()

  try {
    const response = await httpPost<{ token: string; user_id: number; username: string }>(
      '/login/',
      { username: email.value, password: password.value },
      false
    )

    if (!response?.token) {
      toast.error('Invalid credentials')
      return
    }

    const cookie = useCookie('auth_token')
    const authUser = useCookie<User>('auth_user')
    cookie.value = response.token

    const user = await $fetch<User>(`${config.public.apiBaseUrl}/me/`, {
      headers: { Authorization: `Token ${response.token}` },
    })

    userStore.setUser(user)
    authUser.value = user
    toast.success('Login successful!')
    navigateTo('/')
  } catch (err: any) {
    console.log(err, "error")

    if (err.status === 403) {
      if (err?.errors?.is_verified === false) {
        userEmail.value = email.value
        dialogMessage.value = err?.errors?.error || 'Your account is not verified. Please check your email for verification instructions.'
        showResendOption.value = true
        openInactiveAccountDialog.value = true
      } else {
        dialogMessage.value = err?.errors?.error || 'Your account approval is pending. We will get back to you as soon as the verification is complete. Thank you for your patience. Please contact our support team for any queries'
        showResendOption.value = false
        openInactiveAccountDialog.value = true
      }
    } else {
      const message =
        err?.errors?.non_field_errors?.[0] ||
        err?.errors?.error ||
        err?.errors?.detail ||
        err?.message ||
        'Login failed. Please try again.'
      toast.error(message)
    }
  } finally {
    loading.value = false
  }
}

const handleResendVerification = async () => {
  if (resendLoading.value) return
  resendLoading.value = true

  const { httpPost } = useHttpClient()

  try {
    const response = await httpPost<{ message: string }>(
      '/resend-verification/',
      { email: userEmail.value },
      false
    )

    if (response?.message) {
      toast.success(response.message)
      openInactiveAccountDialog.value = false
    }
  } catch (err: any) {
    const message =
      err?.errors?.error ||
      err?.errors?.detail ||
      err?.message ||
      'Failed to resend verification email. Please try again.'
    toast.error(message)
  } finally {
    resendLoading.value = false
  }
}

onMounted(async () => {
  const route = useRoute()
  const token = route.query.token as string | undefined
  if (!token) return

  const cookie = useCookie('auth_token')
  const authUser = useCookie<User>('auth_user')
  const userStore = useUserStore()

  try {
    const user = await $fetch<User>(`${config.public.apiBaseUrl}/me/`, {
      headers: { Authorization: `Token ${token}` },
    })

    cookie.value = token
    authUser.value = user
    userStore.setUser(user)

    toast.success('Email verified! Logged in successfully.')
    navigateTo('/')
  } catch (err: any) {
    console.log(err,"error")

    if (err.status === 403) {
      dialogMessage.value = 'Your account approval is pending. We will get back to you as soon as the verification is complete. Thank you for your patience. Please contact our support team for any queries'
      openInactiveAccountDialog.value = true
    } else if (err.data?.error) {
      toast.error(err.data.error)
    } else {
      toast.error('Verification failed. The link might be invalid or expired.')
    }
  }
})

</script>

<template>
  <div
    class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-tr from-background to-muted px-4"
  >
    <div class="w-full max-w-md">
      <Card>
        <CardHeader class="text-center">
          <CardTitle class="flex items-center justify-center gap-2 text-2xl">
            <LogIn class="w-6 h-6" />
            Welcome Back!
          </CardTitle>
          <CardDescription>
            Sign in to continue to your dashboard
          </CardDescription>
        </CardHeader>

        <CardContent class="space-y-6">
          <form class="space-y-4" @submit.prevent="handleLogin">
            <div class="space-y-2">
              <Label for="email" class="text-sm font-medium">
                Email
              </Label>
              <Input
                id="email"
                v-model="email"
                type="email"
                placeholder="you@example.com"
                required
                autofocus
                class="w-full"
              />
            </div>

            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <Label for="password" class="text-sm font-medium">
                  Password
                </Label>
                <a
                  href="/forgot-password"
                  class="text-sm text-primary font-medium hover:underline"
                >
                  Forgot Password?
                </a>
              </div>
              <div class="relative">
                <Input
                  id="password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  placeholder="••••••••"
                  class="w-full pr-10"
                  @keyup.enter="handleLogin"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  @click="showPassword = !showPassword"
                >
                  <component
                    :is="showPassword ? EyeOff : Eye"
                    class="h-4 w-4 text-muted-foreground"
                  />
                </Button>
              </div>
            </div>

            <Button
              type="submit"
              class="w-full"
              :disabled="loading"
            >
              <span v-if="loading">Signing in...</span>
              <span v-else>Sign In</span>
            </Button>
          </form>
        </CardContent>

        <CardFooter>
          <p class="text-center text-sm text-muted-foreground w-full">
            Don't have an account?
            <a href="/register" class="font-semibold underline underline-offset-4 text-primary">
              Register here
            </a>
          </p>
        </CardFooter>
      </Card>
    </div>

    <Dialog v-model:open="openInactiveAccountDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Account Verification Required</DialogTitle>
          <DialogDescription>{{ dialogMessage }}</DialogDescription>
        </DialogHeader>
        <DialogFooter v-if="showResendOption">
          <div class="flex flex-col gap-2 w-full">
            <Button
              @click="handleResendVerification"
              :disabled="resendLoading"
              class="w-full"
            >
              <span v-if="resendLoading">Sending...</span>
              <span v-else>Resend Verification Email</span>
            </Button>
            <Button
              variant="outline"
              @click="openInactiveAccountDialog = false"
              class="w-full"
            >
              Cancel
            </Button>
          </div>
        </DialogFooter>
        <DialogFooter v-else>
          <Button
            @click="openInactiveAccountDialog = false"
            class="w-full"
          >
            OK
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
