<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '~/stores/user'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Eye, EyeOff } from 'lucide-vue-next'
import { Field as FormField } from 'vee-validate'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'

definePageMeta({
  layout: 'public',
  middleware: ['redirect-if-authenticated'],
})

const userStore = useUserStore()
const form = userStore.getFormInstance()
const { handleSubmit, meta } = form

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const onSubmit = handleSubmit(async (values) => {
  const success = await userStore.register(values)
  if (success) {
    navigateTo('/login')
  }
})

const disabled = computed(() => !meta.value.valid)
</script>

<template>
  <div class="min-h-screen flex flex-col justify-center items-center px-4 sm:px-6">
    <div class="w-full max-w-md backdrop-blur-md rounded-lg shadow-xl border p-6 sm:p-10 bg-card">
      <header class="mb-6 sm:mb-8 text-center">
        <h1 class="text-2xl sm:text-3xl font-extrabold mb-2">Create Account</h1>
        <p class="text-sm sm:text-base">Fill the form below to register</p>
      </header>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <FormField v-slot="{ field }" name="email">
          <FormItem>
            <FormLabel class="flex items-center gap-1">
              Email <RequiredLabel />
            </FormLabel>
            <FormControl>
              <Input v-bind="field" type="email" placeholder="you@example.com" autofocus />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField v-slot="{ field }" name="password">
          <FormItem class="relative">
            <FormLabel class="flex items-center gap-1">
              Password <RequiredLabel />
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

        <Button type="submit" class="w-full font-semibold text-base sm:text-lg rounded-sm shadow-md" :disabled="disabled">
          Register
        </Button>
      </form>

      <p class="mt-6 sm:mt-8 text-center text-sm">
        Already have an account?
        <a href="/login" class="font-semibold underline underline-offset-4">Login here</a>
      </p>
    </div>
  </div>
</template>
