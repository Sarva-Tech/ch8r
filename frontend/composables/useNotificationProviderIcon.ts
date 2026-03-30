import { computed, defineComponent, h } from 'vue'
import { Bell } from 'lucide-vue-next'
import DiscordIcon from '~/components/icons/DiscordIcon.vue'
import SlackIcon from '~/components/icons/SlackIcon.vue'

export function useNotificationProviderIcon(provider: string) {
  return computed(() => {
    switch (provider?.toLowerCase()) {
      case 'discord':
        return DiscordIcon
      case 'slack':
        return SlackIcon
      case 'email':
      default:
        return defineComponent({
          render() {
            return h(Bell, {
              size: 16,
              class: 'text-gray-600',
            })
          },
        })
    }
  })
}
