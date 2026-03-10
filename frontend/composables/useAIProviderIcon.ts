import { computed, defineComponent, h } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import GeminiIcon from '~/components/icons/GeminiIcon.vue'

export function useAIProviderIcon(provider: string) {
  return computed(() => {
    switch (provider?.toLowerCase()) {
      case 'gemini':
        return GeminiIcon
      case 'custom':
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
