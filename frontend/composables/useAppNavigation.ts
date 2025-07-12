import { useRouter } from 'vue-router'

export function useAppNavigation() {
  const router = useRouter()
  const appStore = useApplicationsStore()

  async function selectAndNavigate(app: Application) {
    appStore.selectApplication(app)

    const selectedApp = appStore.selectedApplication
    if (selectedApp) {
      await router.push(`/applications/${selectedApp.uuid}`)
    }
  }

  return { selectAndNavigate }
}
