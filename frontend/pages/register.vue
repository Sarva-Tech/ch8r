<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '~/stores/user'
import C8Button from '@/components/C8Button.vue'
import { Input } from '@/components/ui/input'
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
            Let's get you started
          </CardTitle>
        </CardHeader>

        <CardContent class="space-y-6">
          <form
            class="space-y-4"
            @submit.prevent="onSubmit"
          >
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
