import { defineStore } from 'pinia'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { USER_ID_PREFIX } from '~/lib/consts'
import { applyBackendErrors } from '~/lib/utils'
import { toast } from 'vue-sonner'
import { useHttpClient } from '~/composables/useHttpClient'

export interface User {
  id: number | null
  email: string
  username: string
  name?: string | null
  first_name?: string | null
  last_name?: string | null
}

const registerSchema = z
  .object({
    email: z
      .string()
      .nonempty({ message: 'Required' })
      .email({ message: 'Invalid email address' }),
    password: z
      .string()
      .nonempty({ message: 'Required' })
      .min(8, { message: 'At least 8 characters' }),
    confirm_password: z
      .string()
      .nonempty({ message: 'Required' })
      .min(8, { message: 'At least 8 characters' }),
  })
  .refine((data) => data.password === data.confirm_password, {
    path: ['confirm_password'],
    message: 'Passwords must match',
  })

type RegisterFormValues = z.infer<typeof registerSchema>
const typedRegisterSchema = toTypedSchema(registerSchema)

export const useUserStore = defineStore('user', {
  state: () => ({
    authUser: {
      id: null,
      email: '',
      username: '',
      name: '',
    } as User,
    form: shallowRef<ReturnType<typeof useForm<RegisterFormValues>> | null>(
      null,
    ),
  }),

  actions: {
    initRegisterForm() {
      if (!this.form) {
        this.form = useForm<RegisterFormValues>({
          validationSchema: typedRegisterSchema,
          initialValues: {
            email: '',
            password: '',
            confirm_password: '',
          },
        })
      }
      return this.form
    },

    getFormInstance() {
      return this.initRegisterForm()
    },

    setBackendErrors(errors: Record<string, string[] | string>) {
      const formInstance = this.getFormInstance()
      if (!formInstance) return
      applyBackendErrors(formInstance, errors)
    },

    setUser(user: User) {
      this.authUser.id = user.id
      this.authUser.email = user.email
      this.authUser.username = user.username
      this.authUser.name =
        [user?.first_name, user?.last_name].filter(Boolean).join(' ') || ''
    },

    clearUser() {
      this.authUser = { id: null, email: '', username: '', name: '' }
      if (this.form) {
        this.form.resetForm()
      }
    },

    async register(values: RegisterFormValues) {
      const { httpPost } = useHttpClient()
      await httpPost(
        '/register/',
        {
          email: values.email,
          username: values.email,
          password: values.password,
        },
        false,
      )
      toast.success(
        'A verification link has been sent to your email. Please verify your account to complete registration and log in.',
      )
      return true
    },
  },

  getters: {
    isLoggedIn: (state) => !!state.authUser.id,
    getUser: (state) => state.authUser,
    getToken: () => useCookie('auth_token') || null,
    userIdentifier: (state) => `${USER_ID_PREFIX}_${state.authUser.id}`,
  },
})
