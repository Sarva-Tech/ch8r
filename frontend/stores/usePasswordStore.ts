import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'

export interface PasswordResetValues {
  password: string
  confirm_password: string
}

export const usePasswordStore = defineStore('password', {
  actions: {
    async requestResetLink(values: { email: string }) {
      const { httpPost } = useHttpClient()
      try {
        const response = await httpPost('/forgot-password/', values, false)
        return response
      } catch (error: any) {
        if (error?.response?.data) {
          throw { type: 'validation', errors: error.response.data }
        }
        throw error
      }
    },

    // Confirm password reset using token
    async confirmPasswordReset(token: string, values: PasswordResetValues) {
      const { httpPost } = useHttpClient()
      try {
        return await httpPost('/reset-password/', { token, ...values }, false)
      } catch (error: any) {
        if (error?.response?.data) {
          throw { type: 'validation', errors: error.response.data }
        }
        throw error
      }
    },
  },
})
