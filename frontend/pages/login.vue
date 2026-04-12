<script setup lang="ts">
import { computed, ref } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import C8Button from '@/components/C8Button.vue'
import { z } from 'zod'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm, Field as FormField } from 'vee-validate'
import { FormControl, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import RequiredLabel from '@/components/RequiredLabel.vue'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useHttpClient } from '~/composables/useHttpClient'
import C8APIAlert from '@/components/C8APIAlert.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'

const config = useRuntimeConfig()

const schema = z.object({
  email: z
    .string()
    .nonempty({ message: 'Required' })
    .email({ message: 'Enter a valid email address' }),
  password: z
    .string()
    .nonempty({ message: 'Required' }),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    email: '',
    password: '',
  },
})

const { handleSubmit, meta, isSubmitting } = form

definePageMeta({
  layout: 'public',
  middleware: ['redirect-if-authenticated'],
})

const showPassword = ref(false)
const openInactiveAccountDialog = ref(false)
const dialogMessage = ref('')
const showResendOption = ref(false)
const userEmail = ref('')
const resendLoading = ref(false)
const { apiError, handleError, clearError } = useApiErrorHandling()

const disabled = computed(() => !meta.value.valid)

const onSubmit = handleSubmit(async (values) => {
  clearError()
  const userStore = useUserStore()
  const { httpPost } = useHttpClient()

  try {
    const response = await httpPost<{ token: string, user_id: number, username: string }>(
      '/login/',
      { username: values.email, password: values.password },
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
    console.log(err, 'error')

    if (err.status === 403) {
      if (err?.errors?.is_verified === false) {
        userEmail.value = values.email
        dialogMessage.value = err?.errors?.error || 'Your account is not verified. Please check your email for verification instructions.'
        showResendOption.value = true
        openInactiveAccountDialog.value = true
      } else {
        dialogMessage.value = err?.errors?.error || 'Your account approval is pending. We will get back to you as soon as the verification is complete. Thank you for your patience. Please contact our support team for any queries'
        showResendOption.value = false
        openInactiveAccountDialog.value = true
      }
    } else {
      handleError(err, form)
    }
  }
})

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
    const message
      = err?.errors?.error
        || err?.errors?.detail
        || err?.message
        || 'Failed to resend verification email. Please try again.'
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
    console.log(err, 'error')

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
            Sign in to your ch8r account
          </CardTitle>
        </CardHeader>

        <CardContent class="space-y-6">
          <form
            class="space-y-4"
            @submit.prevent="onSubmit"
          >
            <C8APIAlert :api-error="apiError" />
            <FormField
              v-slot="{ field }"
              name="email"
            >
              <FormItem>
                <FormLabel class="flex items-center gap-1">
                  Email <RequiredLabel />
                </FormLabel>
                <FormControl>
                  <Input
                    v-bind="field"
                    type="email"
                    placeholder="you@example.com"
                    autofocus
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <FormField
              v-slot="{ field }"
              name="password"
            >
              <FormItem>
                <div class="flex justify-between items-center">
                  <FormLabel class="flex items-center gap-1">
                    Password <RequiredLabel />
                  </FormLabel>
                  <a
                    href="/forgot-password"
                    class="text-sm underline"
                  >
                    Forgot Password?
                  </a>
                </div>
                <FormControl>
                  <div class="relative">
                    <Input
                      v-bind="field"
                      :type="showPassword ? 'text' : 'password'"
                      placeholder="password"
                      class="w-full pr-10"
                    />
                    <C8Button
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
                    </C8Button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <C8Button
              type="submit"
              class="w-full"
              :loading="isSubmitting"
              :disabled="disabled"
              label="Sign In"
            />
          </form>
        </CardContent>

        <CardFooter>
          <p class="text-center text-sm text-muted-foreground w-full">
            Don't have an account yet?
            <a
              href="/register"
              class="underline"
              @click.prevent="navigateTo('/register')"
            >
              Sign up
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
            <C8Button
              :loading="resendLoading"
              class="w-full"
              :label="resendLoading ? 'Sending...' : 'Resend Verification Email'"
              @click="handleResendVerification"
            />
            <C8Button
              variant="outline"
              class="w-full"
              label="Cancel"
              @click="openInactiveAccountDialog = false"
            />
          </div>
        </DialogFooter>
        <DialogFooter v-else>
          <C8Button
            class="w-full"
            label="OK"
            @click="openInactiveAccountDialog = false"
          />
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
