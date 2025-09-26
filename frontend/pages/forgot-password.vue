<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePasswordStore } from '@/stores/usePasswordStore'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Field as FormField, useForm } from 'vee-validate'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { z } from 'zod'
import { toTypedSchema } from '@vee-validate/zod'

definePageMeta({
  layout: 'public',
})

const router = useRouter()
const passwordStore = usePasswordStore()

const schema = z.object({
  email: z
    .string()
    .nonempty({ message: 'Email is required' })
    .email({ message: 'Enter a valid email address' }),
})
const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    email: '',
  },
})

const { handleSubmit, meta, validate } = form

const onSubmit = handleSubmit(async (values) => {
  try {
    await passwordStore.requestResetLink(values)
    toast.success('Password reset link sent! Check your email.')
    await router.push('/login')
  } catch (e: never) {
    console.log(e.errors)
    toast.error('Failed to send password reset link.')
  }
})

onMounted(() => {
  validate()
})

const disabled = computed(() => !meta.value.valid)
</script>

<template>
  <div class="min-h-screen flex flex-col justify-center items-center px-4 sm:px-6">
    <div
      class="w-full max-w-md backdrop-blur-md rounded-lg shadow-xl border p-6 sm:p-10 bg-card"
    >
      <header class="mb-6 sm:mb-8 text-center">
        <h1 class="text-2xl sm:text-3xl font-extrabold mb-2">Forgot Password?</h1>
        <p class="text-sm sm:text-base">
          Enter your email and we’ll send you a password reset link.
        </p>
      </header>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <FormField v-slot="{ field }" name="email">
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

        <Button
          type="submit"
          class="w-full font-semibold text-base sm:text-lg rounded-sm shadow-md"
          :disabled="disabled"
        >
          Send Reset Link
        </Button>
      </form>

      <p class="mt-6 sm:mt-8 text-center text-sm">
        Remembered your password?
        <a href="/login" class="font-semibold underline underline-offset-4">Login</a>
      </p>
    </div>
  </div>
</template>
