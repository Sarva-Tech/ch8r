export default defineNuxtRouteMiddleware(async (to) => {
  const userStore = useUserStore();
  if(!userStore.getToken?.value) return

  const excludedRoutes = ['/login', '/register', '/forgot-password', '/reset-password', '/verify-email']
  const isExcludedRoute = excludedRoutes.some(route => to.path.startsWith(route))

  if (isExcludedRoute) return

  const appStore = useApplicationsStore()
  const chatroomStore = useChatroomStore()
  const chatroomMessagesStore = useChatroomMessagesStore()

  const appId = to.params.appId as string | undefined
  const chatroomId = to.params.chatroomId as string | undefined

  if (!appStore.applications.length) {
    await appStore.fetchApplications()
  }

  const apps = appStore.applications
  if (appId) {
    const appToBeSelected = apps.find((app) => app?.uuid === appId)
    if (appToBeSelected) {
      appStore.selectApplication(appToBeSelected)

      if (!chatroomStore.chatrooms.length) {
        await chatroomStore.fetchChatrooms(appToBeSelected.uuid)
      }

      if (chatroomId) {
        await chatroomMessagesStore.selectChatroom(appToBeSelected.uuid, chatroomId)
      }
    }
  }
})
