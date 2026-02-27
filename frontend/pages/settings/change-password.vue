<script setup lang="ts">
import { ref, computed } from 'vue'
import { Eye, EyeOff, Lock, CheckCircle } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useHttpClient } from '~/composables/useHttpClient'

definePageMeta({
  layout: 'default',
})

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const success = ref(false)

const { httpPost } = useHttpClient()

const validatePasswords = () => {
  const errors = []

  if (newPassword.value.length < 8) {
    errors.push('New password must be at least 8 characters long')
  }

  if (!/[a-z]/.test(newPassword.value) || !/[A-Z]/.test(newPassword.value)) {
    errors.push('Password must contain both uppercase and lowercase letters')
  }

  if (!/[0-9]/.test(newPassword.value)) {
    errors.push('Password must contain at least one number')
  }

  if (!/[^a-zA-Z0-9]/.test(newPassword.value)) {
    errors.push('Password must contain at least one special character')
  }

  if (newPassword.value !== confirmPassword.value) {
    errors.push('New passwords do not match')
  }

  if (currentPassword.value === newPassword.value) {
    errors.push('New password must be different from current password')
  }

  if (errors.length > 0) {
    errors.forEach(error => toast.error(error))
    return false
  }

  return true
}

const handlePasswordChange = async () => {
  if (loading.value) return

  if (!validatePasswords()) return

  loading.value = true

  try {
    const response = await httpPost<{ message: string; token: string }>(
      '/change-password/',
      {
        current_password: currentPassword.value,
        new_password: newPassword.value,
        confirm_password: confirmPassword.value,
      }
    )

    if (response?.message) {
      success.value = true
      toast.success('Password changed successfully!')

      if (response.token) {
        const cookie = useCookie('auth_token')
        cookie.value = response.token
      }

      setTimeout(() => {
        currentPassword.value = ''
        newPassword.value = ''
        confirmPassword.value = ''
        success.value = false
      }, 3000)
    }
  } catch (err: any) {
    console.error('Password change error:', err)

    const errors = err?.errors || {}

    if (errors.current_password) {
      toast.error(errors.current_password[0] || 'Current password is incorrect')
    } else if (errors.new_password) {
      toast.error(errors.new_password[0] || 'New password is not valid')
    } else if (errors.non_field_errors) {
      toast.error(errors.non_field_errors[0] || 'Password change failed')
    } else if (errors.error) {
      toast.error(errors.error)
    } else {
      toast.error('Failed to change password. Please try again.')
    }
  } finally {
    loading.value = false
  }
}

const passwordStrength = computed(() => {
  const password = newPassword.value
  if (!password) return { score: 0, text: '', color: '' }

  let score = 0
  if (password.length >= 8) score++
  if (password.length >= 12) score++
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^a-zA-Z0-9]/.test(password)) score++

  const strengthLevels = [
    { score: 0, text: 'Very Weak', color: 'text-red-500' },
    { score: 1, text: 'Weak', color: 'text-red-400' },
    { score: 2, text: 'Fair', color: 'text-yellow-500' },
    { score: 3, text: 'Good', color: 'text-blue-500' },
    { score: 4, text: 'Strong', color: 'text-green-500' },
    { score: 5, text: 'Very Strong', color: 'text-green-600' }
  ]

  return strengthLevels[Math.min(score, 4)]
})
</script>

<template>
  <div class="container max-w-2xl mx-auto py-8 px-4 pt-[72px]">
    <div class="mb-8">
      <h1 class="text-3xl font-bold tracking-tight">Change Password</h1>
      <p class="text-muted-foreground mt-2">
        Update your password to keep your account secure
      </p>
    </div>

    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Lock class="w-5 h-5" />
          Password Settings
        </CardTitle>
        <CardDescription>
          Choose a strong password that you haven't used before
        </CardDescription>
      </CardHeader>

      <CardContent class="space-y-6">
        <Alert v-if="success" class="border-green-200 bg-green-50 text-green-800">
          <CheckCircle class="h-4 w-4" />
          <AlertDescription>
            Your password has been changed successfully!
          </AlertDescription>
        </Alert>

        <div class="space-y-2">
          <Label for="current-password" class="text-sm font-medium">
            Current Password
          </Label>
          <div class="relative">
            <Input
              id="current-password"
              v-model="currentPassword"
              :type="showCurrentPassword ? 'text' : 'password'"
              placeholder="Enter your current password"
              class="pr-10"
              :disabled="loading"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
              @click="showCurrentPassword = !showCurrentPassword"
            >
              <component
                :is="showCurrentPassword ? EyeOff : Eye"
                class="h-4 w-4 text-muted-foreground"
              />
            </Button>
          </div>
        </div>

        <div class="space-y-2">
          <Label for="new-password" class="text-sm font-medium">
            New Password
          </Label>
          <div class="relative">
            <Input
              id="new-password"
              v-model="newPassword"
              :type="showNewPassword ? 'text' : 'password'"
              placeholder="Enter your new password"
              class="pr-10"
              :disabled="loading"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
              @click="showNewPassword = !showNewPassword"
            >
              <component
                :is="showNewPassword ? EyeOff : Eye"
                class="h-4 w-4 text-muted-foreground"
              />
            </Button>
          </div>

          <div v-if="newPassword" class="mt-2">
            <div class="flex items-center justify-between text-xs">
              <span :class="passwordStrength.color">
                Password strength: {{ passwordStrength.text }}
              </span>
            </div>
            <div class="mt-1 h-2 w-full bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full transition-all duration-300 ease-out"
                :class="{
                  'bg-red-500': passwordStrength.score <= 1,
                  'bg-yellow-500': passwordStrength.score === 2,
                  'bg-blue-500': passwordStrength.score === 3,
                  'bg-green-500': passwordStrength.score >= 4
                }"
                :style="{ width: `${(passwordStrength.score / 5) * 100}%` }"
              />
            </div>
          </div>
        </div>

        <div class="space-y-2">
          <Label for="confirm-password" class="text-sm font-medium">
            Confirm New Password
          </Label>
          <div class="relative">
            <Input
              id="confirm-password"
              v-model="confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="Confirm your new password"
              class="pr-10"
              :disabled="loading"
            />
            <Button
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
            </Button>
          </div>
        </div>

        <div class="bg-muted/50 rounded-lg p-4">
          <h4 class="text-sm font-medium mb-2">Password Requirements:</h4>
          <ul class="text-xs text-muted-foreground space-y-1">
            <li :class="{ 'text-green-600': newPassword.length >= 8 }">
              {{ newPassword.length >= 8 ? '✓' : '○' }} At least 8 characters long
            </li>
            <li :class="{ 'text-green-600': /[a-z]/.test(newPassword) && /[A-Z]/.test(newPassword) }">
              {{ /[a-z]/.test(newPassword) && /[A-Z]/.test(newPassword) ? '✓' : '○' }} Contains both uppercase and lowercase letters
            </li>
            <li :class="{ 'text-green-600': /[0-9]/.test(newPassword) }">
              {{ /[0-9]/.test(newPassword) ? '✓' : '○' }} Contains at least one number
            </li>
            <li :class="{ 'text-green-600': /[^a-zA-Z0-9]/.test(newPassword) }">
              {{ /[^a-zA-Z0-9]/.test(newPassword) ? '✓' : '○' }} Contains at least one special character
            </li>
            <li :class="{ 'text-green-600': confirmPassword && newPassword === confirmPassword }">
              {{ confirmPassword && newPassword === confirmPassword ? '✓' : '○' }} Passwords match
            </li>
          </ul>
        </div>
      </CardContent>

      <CardFooter>
        <Button
          @click="handlePasswordChange"
          :disabled="loading || !currentPassword || !newPassword || !confirmPassword"
          class="w-full"
        >
          <span v-if="loading">Changing Password...</span>
          <span v-else>Change Password</span>
        </Button>
      </CardFooter>
    </Card>
  </div>
</template>
