 <template>
  <div class="mt-8 space-y-6">
    <div
      v-for="(items, type) in notificationItems"
      :key="type"
      class="space-y-3"
    >
      <ul class="space-y-2">
        <li
          v-for="item in items"
          :key="item.id"
          class="flex justify-between items-center p-3 bg-muted rounded-lg group hover:bg-muted/80 transition-colors"
        >
          <div class="flex flex-col min-w-0 flex-1">
            <span class="text-sm font-medium truncate">{{ item.profileName }}</span>
            <span class="text-xs text-muted-foreground truncate">{{ item.value }}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            class="flex-shrink-0 text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100"
            :aria-label="`Remove ${item.profileName} ${type} profile`"
            @click="$emit('remove', item.id)"
          >
            <Trash2Icon class="h-4 w-4" />
          </Button>
        </li>
      </ul>
    </div>

    <div
      v-if="hasNoItems"
      class="text-center py-8 text-muted-foreground"
    >
      <p>No notification profiles added yet</p>
      <p class="text-sm">Add profiles using the form above</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '~/components/ui/button'
import { Trash2Icon } from 'lucide-vue-next'

export interface NotificationItem {
  id: string
  profileName: string
  value: string
}

export interface NotificationItems {
  discord: NotificationItem[]
  slack: NotificationItem[]
  email: NotificationItem[]
}

const props = defineProps<{
  items: NotificationItems
}>()
defineEmits<{
  remove: [id: string]
}>()

const notificationItems = computed(() => {
  return Object.entries(props.items)
    .filter(([_, items]) => items.length > 0)
    .reduce((acc, [type, items]) => {
      acc[type] = items
      return acc
    }, {} as Record<string, NotificationItem[]>)
})

const hasNoItems = computed(() => {
  return Object.values(props.items).every(items => items.length === 0)
})
</script>

<style scoped>
.min-w-0 {
  min-width: 0;
}
</style>