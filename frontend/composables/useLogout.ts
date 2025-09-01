import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

export function useLogout() {
  const router = useRouter()
  const userStore = useUserStore()

  function clearCookie(name: string) {
    document.cookie = `${name}=; path=/; max-age=0`
  }

  function logout() {
    userStore.clearUser()
    clearCookie('auth_token')
    clearCookie('auth_user')

    if (router) {
      router.push('/login')
    } else {
      window.location = '/login'
    }
  }

  return {
    logout,
  }
}
