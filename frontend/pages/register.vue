<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '~/stores/user'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff, UserPlus } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
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
  <div class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-tr from-background to-muted px-4">
    <div class="w-full max-w-md">
      <Card>
        <CardHeader class="text-center">
          <CardTitle class="flex items-center justify-center gap-2 text-2xl">
            <UserPlus class="w-6 h-6" />
            Create Account
          </CardTitle>
          <CardDescription>
            Fill the form below to register
          </CardDescription>
        </CardHeader>

        <CardContent class="space-y-6">
          <form class="space-y-4" @submit.prevent="onSubmit">
            <FormField v-slot="{ field }" name="email">
              <FormItem>
                <FormLabel class="flex items-center gap-1">
                  Email <RequiredLabel />
                </FormLabel>
                <FormControl>
                  <Input v-bind="field" type="email" placeholder="you@example.com" autofocus class="w-full" />
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
                    class="w-full pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    @click="showPassword = !showPassword"
                  >
                    <component :is="showPassword ? EyeOff : Eye" class="h-4 w-4 text-muted-foreground" />
                  </Button>
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
                    class="w-full pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    @click="showConfirmPassword = !showConfirmPassword"
                  >
                    <component :is="showPassword ? EyeOff : Eye" class="h-4 w-4 text-muted-foreground" />
                  </Button>
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <Button
              type="submit"
              class="w-full"
              :disabled="disabled"
            >
              Create Account
            </Button>
          </form>
        </CardContent>

        <CardFooter>
          <p class="text-center text-sm text-muted-foreground w-full">
            Already have an account?
            <a href="/login" class="font-semibold underline underline-offset-4 text-primary">
              Sign in here
            </a>
          </p>
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
