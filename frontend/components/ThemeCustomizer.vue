<script lang="ts" setup>
import { Moon, Sun } from 'lucide-vue-next'
import { Button } from "@/components/ui/button"
import { Label } from '@/components/ui/label'

const colorMode = useColorMode()
const isDark = computed(() => colorMode.value === 'dark')
</script>

<template>
  <div class="flex flex-col space-y-4 md:space-y-6">
    <div class="flex items-start pt-4 md:pt-0">
      <div class="space-y-1 pr-2">
        <div class="font-semibold leading-none tracking-tight">
          Theme Customizer
        </div>
      </div>
    </div>
    <div class="flex flex-1 flex-col space-y-4 md:space-y-6">
      <div class="space-y-1.5 ">
        <Label for="theme" class="text-xs"> Theme </Label>
        <div class="flex space-x-2">
          <Button
            class="h-8"
            variant="outline"
            :class="{ 'border-2 border-foreground': !isDark }"
            @click="colorMode.preference = 'light'"
          >
            <Sun class="w-4 h-4 mr-2" />
            <span class="text-xs">Light</span>
          </Button>
          <Button
            class="h-8"
            variant="outline"
            :class="{ 'border-2 border-foreground': isDark }"
            @click="colorMode.preference = 'dark'"
          >
            <Moon class="w-4 h-4 mr-2" />
            <span class="text-xs">Dark</span>
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
