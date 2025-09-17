<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Eye, EyeOff } from 'lucide-vue-next'
import { Field as FormField, useForm } from 'vee-validate'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { toast } from 'vue-sonner'

definePageMeta({
  layout: 'public',
})

const route = useRoute()
const token = route.query.token as string | undefined
const passwordStore = usePasswordStore()

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const schema = z
  .object({
    password: z
      .string()
      .nonempty({ message: 'Password is required' })
      .min(8, { message: 'Password must be at least 8 characters' }),
    confirm_password: z.string().nonempty({ message: 'Confirm password is required' }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  })

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    password: '',
    confirm_password: '',
  },
})
const { isSubmitting, meta, handleSubmit } = form

const onSubmit = handleSubmit(async (values) => {
  if (!token) {
    toast.error('Invalid or missing token.')
    return
  }

  try {
    await passwordStore.confirmPasswordReset(token, values)
    toast.success('Password reset successfully. Please login.')
    navigateTo('/login')
  } catch (e: any) {
    console.log(e)
    toast.error('Failed to reset password.')
  }
})


const disabled = computed(() => !meta.value.valid)
</script>

<template>
  <div class="min-h-screen flex flex-col justify-center items-center px-4 sm:px-6">
    <div class="w-full max-w-md backdrop-blur-md rounded-lg shadow-xl border p-6 sm:p-10 bg-card">
      <header class="mb-6 sm:mb-8 text-center">
        <h1 class="text-2xl sm:text-3xl font-extrabold mb-2">Reset Password</h1>
        <p class="text-sm sm:text-base">Enter your new password below.</p>
      </header>

      <!-- ✅ Vee-validate form -->
      <form class="space-y-4" @submit.prevent="onSubmit">
        <!-- New Password -->
        <FormField v-slot="{ field }" name="password">
          <FormItem class="relative">
            <FormLabel class="flex items-center gap-1">
              New Password <RequiredLabel />
            </FormLabel>
            <FormControl>
              <Input
                v-bind="field"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                class="pr-10"
              />
              <button
                type="button"
                class="absolute right-3 top-9 focus:outline-none"
                @click="showPassword = !showPassword"
              >
                <component :is="showPassword ? Eye : EyeOff" class="w-5 h-5" />
              </button>
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- Confirm Password -->
        <FormField v-slot="{ field }" name="confirm_password">
          <FormItem class="relative">
            <FormLabel class="flex items-center gap-1">
              Confirm Password <RequiredLabel />
            </FormLabel>
            <FormControl>
              <Input
                v-bind="field"
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="••••••••"
                class="pr-10"
              />
              <button
                type="button"
                class="absolute right-3 top-9 focus:outline-none"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <component :is="showConfirmPassword ? Eye : EyeOff" class="w-5 h-5" />
              </button>
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <!-- Submit Button -->
        <Button
          type="submit"
          class="w-full font-semibold text-base sm:text-lg rounded-sm shadow-md"
          :disabled="disabled || isSubmitting"
          :loading="isSubmitting"
        >
          Change Password
        </Button>
      </form>
    </div>
  </div>
</template>
