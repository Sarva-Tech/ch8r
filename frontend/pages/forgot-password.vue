<script setup lang="ts">
import { computed } from 'vue'
import { usePasswordStore } from '@/stores/usePasswordStore'
import { Input } from '@/components/ui/input'
import C8Button from '@/components/C8Button.vue'
import { Field as FormField, useForm } from 'vee-validate'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { z } from 'zod'
import C8APIAlert from '@/components/C8APIAlert.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { toTypedSchema } from '@vee-validate/zod'

definePageMeta({
  layout: 'public',
})

const router = useRouter()
const passwordStore = usePasswordStore()

const schema = z.object({
  email: z
    .string()
    .nonempty({ message: 'Required' })
    .email({ message: 'Enter a valid email address' }),
})
const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    email: '',
  },
})
const { handleSubmit, meta, isSubmitting } = form
const { apiError, handleError, clearError } = useApiErrorHandling()

const onSubmit = handleSubmit(async (values) => {
  clearError()
  try {
    await passwordStore.requestResetLink(values)
    toast.success('Password reset link sent! Check your email.')
    await router.push('/login')
  } catch (e: unknown) {
    handleError(e, form)
  }
})

const disabled = computed(() => !meta.value.valid)
</script>

<template>
  <div class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-tr from-background to-muted px-4">
    <div class="w-full max-w-md">
      <Card>
        <CardHeader class="text-center">
          <CardTitle class="flex items-center justify-center gap-2 text-2xl">
            Reset Password
          </CardTitle>
          <CardDescription>
            We'll email you instructions on how to reset your password.
          </CardDescription>
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
                    placeholder="hi@ch8r.com"
                    autofocus
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <C8Button
              type="submit"
              class="w-full"
              :loading="isSubmitting"
              :disabled="disabled"
              label="Reset Password"
            />
          </form>
        </CardContent>

        <CardFooter>
          <p class="text-center text-sm text-muted-foreground w-full">
            Remember your password?
            <a
              href="/login"
              class="underline"
              @click.prevent="navigateTo('/login')"
            >
              Login
            </a>
          </p>
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
