<script setup lang="ts">
import { ref, computed } from 'vue'
import { useForm, Field as FormField } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { useUserStore } from '~/stores/user'
import C8Button from '@/components/C8Button.vue'
import { Input } from '@/components/ui/input'
import { Eye, EyeOff } from 'lucide-vue-next'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '@/components/C8APIAlert.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'

definePageMeta({
  layout: 'public',
  middleware: ['redirect-if-authenticated'],
})

const registerSchema = z
  .object({
    username: z.string().nonempty({ message: 'Required' }).email({ message: 'Invalid email address' }),
    password: z.string().nonempty({ message: 'Required' }).min(8, { message: 'At least 8 characters' }),
    confirm_password: z.string().nonempty({ message: 'Required' }).min(8, { message: 'At least 8 characters' }),
  })
  .refine(data => data.password === data.confirm_password, {
    path: ['confirm_password'],
    message: 'Passwords must match',
  })

const userStore = useUserStore()
const form = useForm({
  validationSchema: toTypedSchema(registerSchema),
  initialValues: {
    username: '',
    password: '',
    confirm_password: '',
  },
})
const { handleSubmit, meta, isSubmitting } = form

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const { apiError, handleError, clearError } = useApiErrorHandling()

const onSubmit = handleSubmit(async (values) => {
  clearError()
  try {
    const success = await userStore.register({
      email: values.username,
      password: values.password,
    })
    if (success) {
      navigateTo('/login')
    }
  } catch (err: unknown) {
    handleError(err, form)
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
            Let's get you started
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
              name="username"
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
                    class="w-full"
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
                <FormLabel class="flex items-center gap-1">
                  Password <RequiredLabel />
                </FormLabel>
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

            <FormField
              v-slot="{ field }"
              name="confirm_password"
            >
              <FormItem>
                <FormLabel class="flex items-center gap-1">
                  Confirm Password <RequiredLabel />
                </FormLabel>
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
                      <component
                        :is="showConfirmPassword ? EyeOff : Eye"
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
              label="Sign up"
            />
          </form>
        </CardContent>

        <CardFooter>
          <p class="text-center text-sm text-muted-foreground w-full">
            Already have an account?
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
