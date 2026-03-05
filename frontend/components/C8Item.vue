<template>
  <div class="flex flex-col gap-6" :class="containerClass">
    <Item :variant="variant" :class="itemClass">
      <ItemMedia v-if="icon" variant="icon">
        <component :is="icon" />
      </ItemMedia>
      
      <ItemContent>
        <ItemTitle>
          <slot name="title" />
        </ItemTitle>
        <ItemDescription>
          <slot name="details" />
        </ItemDescription>
      </ItemContent>
      
      <ItemActions v-if="hasActions || $slots.actions || $slots.dropdown">
        <slot name="actions">
          <DropdownMenu v-if="$slots.dropdown">
            <DropdownMenuTrigger as-child>
              <Button size="sm" variant="outline" class="h-8 w-8 p-0">
                <EllipsisVertical class="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <slot name="dropdown" />
            </DropdownMenuContent>
          </DropdownMenu>
        </slot>
      </ItemActions>
    </Item>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { EllipsisVertical } from 'lucide-vue-next'
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemMedia,
  ItemTitle,
  ItemActions,
} from '~/components/ui/item'
import { Button } from '~/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu'
import type { ItemVariants } from '~/components/ui/item'

interface Props {
  variant?: ItemVariants['variant']
  icon?: Component | null
  itemClass?: string
  containerClass?: string
  hasActions?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'outline',
  icon: null,
  itemClass: '',
  containerClass: 'w-full max-w-lg',
  hasActions: true,
})
</script>
