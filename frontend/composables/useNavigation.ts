export function useNavigation() {
  const appStore = useApplicationsStore()
  const chatroomMessages = useChatroomMessagesStore()
  async function selectAppAndNavigate(app: Application) {
    appStore.selectApplication(app)

    const selectedApp = appStore.selectedApplication
    if (selectedApp) {
      await navigateTo(`/applications/${selectedApp.uuid}`)
    }
  }

  async function selectChatroomAndNavigate(app: Application, chatroom: ChatroomPreview) {
    if (app && chatroom) {
      await chatroomMessages.selectChatroom(
        app.uuid,
        chatroom.uuid
      )
      await navigateTo(`/applications/${app.uuid}/messages/${chatroom.uuid}`)
    }
  }


  return { selectAppAndNavigate, selectChatroomAndNavigate }
}
