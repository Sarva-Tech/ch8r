<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import C8Button from '@/components/C8Button.vue'
import { Input } from '@/components/ui/input'
import { Eye, EyeOff } from 'lucide-vue-next'
import { Field as FormField, useForm } from 'vee-validate'
import { FormControl, FormItem, FormMessage } from '~/components/ui/form'
import C8Label from '@/components/C8Label.vue'
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

      <form class="space-y-4" @submit.prevent="onSubmit">
        <FormField v-slot="{ field }" name="password">
          <FormItem>
            <C8Label message="New Password" required />
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
                  <component :is="showPassword ? EyeOff : Eye" class="h-4 w-4 text-muted-foreground" />
                </C8Button>
              </div>
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>
        <FormField v-slot="{ field }" name="confirm_password">
          <FormItem>
            <C8Label message="Confirm Password" required />
            <FormControl>
              <div class="relative">
                <Input
                  v-bind="field"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="password"
                  class="w-full pr-10"
                />
                <C8Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <component :is="showConfirmPassword ? EyeOff : Eye" class="h-4 w-4 text-muted-foreground" />
                </C8Button>
              </div>
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>
        <C8Button
          type="submit"
          class="w-full font-semibold text-base sm:text-lg rounded-sm shadow-md"
          :disabled="disabled"
          :loading="isSubmitting"
          label="Change Password"
        />
      </form>
    </div>
  </div>
</template>
