<template>
  <form class="space-y-5">
    <FormField v-slot="{ componentField }" name="name">
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            Connection Name
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            placeholder="Ch8r Dev"
          />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>

    <C8Select
      :options="modelTypes"
      :model-value="selectedModelType"
      label="Model Purpose"
      @update:model-value="val => selectedModelType = val"
    />

    <FormField v-slot="{ componentField }" name="base_url">
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            Base URL
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            placeholder="https://api.openai.com/v1"
          />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>

    <FormField v-slot="{ componentField }" name="api_key">
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            API Key
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            type="password"
            placeholder="org-YvnH2WW0YjzHn0gAUzh7JY3q"
          />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>

    <FormField v-slot="{ componentField }" name="model_name">
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            Model Name
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            placeholder="gpt-5"
          />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { Field as FormField } from 'vee-validate'
import C8Select from '~/components/C8Select.vue'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'

const modelStore = useModelStore()

const modelTypes = [
  { label: 'Text Generation', value: 'text'},
  { label: 'Embedding', value: 'embedding'},
  { label: 'Re-ranking', value: 'reranking'},
]

const selectedModelType = ref(modelTypes[0])

const { defineField } = modelStore.initForm()

const [model_type] = defineField('model_type')

watch(selectedModelType, (val) => {
  model_type.value = val.value
}, { immediate: true })
</script>
