<script setup lang="ts">
import { Paintbrush } from 'lucide-vue-next'
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

</script>

<template>
  <Popover>
    <PopoverTrigger as-child>
      <Button
        class="w-8 h-8"
        :variant="'ghost'"
        :size="'icon'"
      >
        <Paintbrush class="w-4 h-4" />
      </Button>
    </PopoverTrigger>
    <PopoverContent :side-offset="8" align="end" class="w-96">
      <ThemeCustomizer />
    </PopoverContent>
  </Popover>
</template>
