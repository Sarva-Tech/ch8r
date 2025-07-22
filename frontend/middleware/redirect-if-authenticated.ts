export default defineNuxtRouteMiddleware(() => {
  const token = useCookie('auth_token')
  if (token.value) {
    return navigateTo('/')
  }
})
