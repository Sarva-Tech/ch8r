<template>
  <FormField v-slot="{ componentField }" name="token">
    <FormItem>
      <FormLabel class="flex items-center">
        <div>
          Token
          <RequiredLabel />
        </div>
      </FormLabel>
      <FormControl>
        <Input v-bind="componentField" placeholder="GitHub Token" />
      </FormControl>
      <FormMessage />
    </FormItem>
  </FormField>

</template>
<script setup lang="ts">
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import type { FormContext } from 'vee-validate'

defineProps<{
  form: FormContext
}>()
</script>
