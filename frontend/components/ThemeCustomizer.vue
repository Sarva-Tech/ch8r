<script lang="ts" setup>
import { Moon, Sun } from 'lucide-vue-next'
import { Button } from "@/components/ui/button"
import { Label } from '@/components/ui/label'
import { AVAILABLE_COLORS } from '~/lib/consts'

const colorMode = useColorMode()
const themeStore = useThemeStore()

const selectedTheme = computed(() => themeStore.currentTheme)
const isDark = computed(() => colorMode.value === 'dark')

const updateTheme = (color: string) => {
  themeStore.setTheme(color)
}
</script>

<template>
  <div class="flex flex-col space-y-4 md:space-y-6">
    <div class="flex flex-1 flex-col space-y-4 md:space-y-6">
      <div class="space-y-2">
        <Label for="theme" class="text-xs"> Theme </Label>
        <div class="flex gap-2">
          <Button
            class="flex items-center min-w-fit justify-start"
            variant="outline"
            size="sm"
            :class="{ 'border-2 border-foreground': !isDark }"
            @click="colorMode.preference = 'light'"
          >
            <Sun class="w-4 h-4 mr-2" />
            <span class="text-xs">Light</span>
          </Button>
          <Button
            class="flex items-center min-w-fit justify-start"
            variant="outline"
            size="sm"
            :class="{ 'border-2 border-foreground ring': isDark }"
            @click="colorMode.preference = 'dark'"
          >
            <Moon class="w-4 h-4" />
            <span class="text-xs">Dark</span>
          </Button>
        </div>
      </div>
      <div class="space-y-2">
        <Label for="theme-color" class="text-xs"> Color </Label>
        <div class="flex flex-wrap gap-2">
          <Button
            v-for="color in AVAILABLE_COLORS"
            :key="color.id"
            class="flex items-center min-w-fit justify-start"
            variant="outline"
            size="sm"
            :class="{ 'border-foreground ring': selectedTheme === color.id }"
            @click="updateTheme(color.id)"
          >
            <span
              class="w-4 h-4 rounded-full"
              :style="{ backgroundColor: color.preview }"
            />
            <span class="text-xs capitalize">{{ color.label }}</span>
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
