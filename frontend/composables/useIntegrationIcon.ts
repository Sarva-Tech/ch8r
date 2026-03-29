import { computed, defineComponent, h } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import GitHubIcon from '~/components/icons/GitHubIcon.vue'

export function useIntegrationIcon(provider: string) {
  return computed(() => {
    switch (provider?.toLowerCase()) {
      case 'github':
        return GitHubIcon
      default:
        return defineComponent({
          render() {
            return h(Sparkles, {
              size: 24,
              class: 'text-gray-600',
            })
          },
        })
    }
  })
}
