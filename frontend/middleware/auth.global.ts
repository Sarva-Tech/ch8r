export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie('auth_token')

  const publicPages = ['/login', '/register', '/forgot-password', '/reset-password']

  if (publicPages.includes(to.path)) return

  if (!token.value) {
    return navigateTo('/login')
  }
})
