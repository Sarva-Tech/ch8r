<script setup lang="ts">
import { useEventListener, useMediaQuery, useVModel } from '@vueuse/core'
import { TooltipProvider } from 'reka-ui'
import { computed,   ref } from 'vue'
import type { HTMLAttributes, Ref } from 'vue';
import { cn } from '@/lib/utils'
import { provideSidebarContext, SIDEBAR_COOKIE_MAX_AGE, SIDEBAR_COOKIE_NAME, SIDEBAR_KEYBOARD_SHORTCUT, SIDEBAR_WIDTH } from './utils'
import ThemePopover from '~/components/ThemePopover.vue'
import { SidebarInset, SidebarTrigger } from '~/components/ui/sidebar/index'
import { useUserStore } from '~/stores/user'

const props = withDefaults(defineProps<{
  defaultOpen?: boolean
  open?: boolean
  class?: HTMLAttributes['class']
}>(), {
  defaultOpen: true,
  open: undefined,
})

const emits = defineEmits<{
  'update:open': [open: boolean]
}>()

const isMobile = useMediaQuery('(max-width: 768px)')
const openMobile = ref(false)

const open = useVModel(props, 'open', emits, {
  defaultValue: props.defaultOpen ?? false,
  passive: (props.open === undefined) as false,
}) as Ref<boolean>

const userStore = useUserStore()
const user = userStore.getUser


function setOpen(value: boolean) {
  open.value = value
  document.cookie = `${SIDEBAR_COOKIE_NAME}=${value}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`
}

function setOpenMobile(value: boolean) {
  openMobile.value = value
}

function toggleSidebar() {
  return isMobile.value ? setOpenMobile(!openMobile.value) : setOpen(!open.value)
}

useEventListener('keydown', (event: KeyboardEvent) => {
  if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
    event.preventDefault()
    toggleSidebar()
  }
})

const state = computed(() => open.value ? 'expanded' : 'collapsed')

const sidebarWidth = computed(() =>
  state.value === 'expanded' ? SIDEBAR_WIDTH : '0rem'
)

provideSidebarContext({
  state,
  open,
  setOpen,
  isMobile,
  openMobile,
  setOpenMobile,
  toggleSidebar,
})
</script>

<template>
  <TooltipProvider :delay-duration="0">
    <div
      data-slot="sidebar-wrapper"
      :style="{
        '--sidebar-width': SIDEBAR_WIDTH,
      }"
      :class="cn('group/sidebar-wrapper has-data-[variant=inset]:bg-sidebar flex min-h-svh w-full', props.class)"
      v-bind="$attrs"
    >
      <slot />
      <SidebarInset>
        <header
          class="fixed top-0 right-0 z-50 flex items-center gap-2 border-b bg-background p-4 justify-between transition-[left] duration-300"
          :style="{ left: isMobile ? '0' : sidebarWidth }"
        >
          <SidebarTrigger class="-ml-1" />
          <div class="flex items-center gap-2">
            <ThemePopover />
            <NavUser :user="user" />
          </div>
        </header>

        <div class="flex flex-col">
          <NuxtPage />
        </div>
      </SidebarInset>
    </div>
  </TooltipProvider>
</template>
