export default defineNuxtRouteMiddleware(async (to) => {
  const appStore = useApplicationsStore()
  const chatroomStore = useChatroomStore()
  const chatroomMessagesStore = useChatroomMessagesStore()

  const appId = to.params.appId as string | undefined
  const chatroomId = to.params.chatroomId as string | undefined

  if (!appStore.applications.length) {
    await appStore.fetchApplications()
  }

  const apps = appStore.applications

  const appToBeSelected = appId
    ? apps.find((app) => app?.uuid === appId)
    : apps[0]

  if (appToBeSelected) {
    appStore.selectApplication(appToBeSelected)

    if (!chatroomStore.chatrooms.length) {
      await chatroomStore.fetchChatrooms(appToBeSelected.uuid)
    }

    if (chatroomId) {
      await chatroomMessagesStore.selectChatroom(appToBeSelected.uuid, chatroomId)
    }
  }
})
