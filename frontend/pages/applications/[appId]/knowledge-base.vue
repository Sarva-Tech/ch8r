<template>
  <div class="flex flex-col h-screen">
    <div class="overflow-y-auto pt-[72px] pb-[120px] p-4">
      <Button variant="outline" @click="ingestApplication">
        Ingest
      </Button>
      <Sheet>
        <SheetTrigger as-child>
          <Button variant="outline">
            Upload KB
          </Button>
        </SheetTrigger>
        <SheetContent class="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Upload Knowledge Base</SheetTitle>
            <SheetDescription>
              Upload knowledge base files to train your AI Agent on your data.
            </SheetDescription>
          </SheetHeader>
          <div class="gap-4 p-4 space-y-6">
            <div class="space-y-4">
              <Label for="name" class="text-right">
                Knowledge Source
              </Label>
              <Select v-model="source">
                <SelectTrigger class="w-full">
                  <SelectValue placeholder="Select Knowledge Source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="youtube">
                      YouTube
                    </SelectItem>
                    <SelectItem value="file">
                      File
                    </SelectItem>
                    <SelectItem value="text">
                      Text
                    </SelectItem>
                    <SelectItem value="URL">
                      URL
                    </SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-4">
              <template v-if="source === 'youtube'">
                <Input v-model="urlInput" type="text" placeholder="YouTube URL" />
              </template>
              <template v-else-if="source === 'file'">
                <Input type="file" @change="onFileChange" />
              </template>
              <template v-else-if="source === 'text'">
                <Textarea v-model="textInput" placeholder="Enter text here..." />
              </template>
              <template v-else-if="source === 'url'">
                <Input v-model="urlInput" type="text" placeholder="URL" />
              </template>
            </div>

          </div>
          <SheetFooter>
            <SheetClose as-child>
              <Button type="submit" @click="handleSubmit">
                Save changes
              </Button>
            </SheetClose>
          </SheetFooter>
        </SheetContent>
      </Sheet>
      <Accordion type="single" class="w-full" collapsible :default-value="knowledgeBase[0]">
        <AccordionItem v-for="item in knowledgeBase" :key="item.uuid" :value="item.path">
          <AccordionTrigger>{{ item.path }}</AccordionTrigger>
          <AccordionContent>
            {{ item }}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  </div>
</template>
<script setup lang="ts">
import { $fetch } from 'ofetch'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '~/components/ui/accordion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const userStore = useUserStore()
const appStore = useApplicationsStore()

const selectedApp = computed(() => appStore.selectedApplication)

const appDetails = ref({})
const knowledgeBase = ref([])

const source = ref('file')
const textInput = ref('')
const urlInput = ref('')
const fileInput = ref<File | null>(null)

onMounted(async () => {
  await loadKB()
})

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  fileInput.value = target.files?.[0] ?? null
}

async function loadKB() {
  try {
    const token = userStore.getToken
    appDetails.value = await $fetch(
      `http://localhost:8000/api/applications/${selectedApp.value?.uuid}/knowledge-bases/`,
      {
        method: 'GET',
        headers: {
          Authorization: `Token ${token.value}`,
          'Content-Type': 'application/json',
        },
      },
    )
    knowledgeBase.value = appDetails.value.application?.knowledge_base
  } catch (err) {
    console.error('Fetch error:', err)
  }
}

const handleSubmit = async () => {
  const formData = new FormData()
  formData.append('source_type', source.value)

  if (source.value === 'file') {
    if (fileInput.value) {
      formData.append('file', fileInput.value)
    }
  } else if (source.value === 'text') {
    formData.append('text', textInput.value)
  } else {
    formData.append('url', urlInput.value)
  }

  try {
    const token = userStore.getToken
    const res = await fetch(`http://localhost:8000/api/applications/${selectedApp.value?.uuid}/knowledge-bases/`, {
      method: 'POST',
      headers: {
        Authorization: `Token ${token.value}`,
      },
      body: formData,
    })

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }

    const result = await res.json()
    console.log('Created KB:', result)
  } catch (err) {
    console.error('Upload failed:', err)
  }
}

const ingestApplication = async () => {
  try {
    const token = userStore.getToken
    const data = await $fetch(
      `http://localhost:8000/api/applications/${selectedApp.value?.uuid}/ingests/`,
      {
        method: 'POST',
        headers: {
          Authorization: `Token ${token.value}`,
          'Content-Type': 'application/json',
        },
      }
    )

    console.log('Ingestion successful:', data)
  } catch (error) {
    console.error('Ingestion failed:', error)
  }
}
</script>
