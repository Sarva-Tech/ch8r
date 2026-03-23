<template>
  <div class="space-y-4">
    <div class="relative">
      <UInput
        v-model="searchQuery"
        placeholder="Search issues, pull requests, discussions..."
        icon="i-heroicons-magnifying-glass-16-solid"
        size="lg"
        @keyup.enter="performSearch"
      />
      <UButton
        v-if="searchQuery"
        icon="i-heroicons-x-mark-16-solid"
        variant="ghost"
        color="gray"
        size="sm"
        class="absolute right-2 top-1/2 transform -translate-y-1/2"
        @click="clearSearch"
      />
    </div>

    <div class="flex items-center justify-between">
      <UButton
        variant="ghost"
        color="gray"
        size="sm"
        icon="i-heroicons-funnel-16-solid"
        @click="showAdvancedFilters = !showAdvancedFilters"
      >
        Advanced Filters
        <UBadge
          v-if="activeFilterCount > 0"
          color="blue"
          variant="solid"
          size="xs"
          class="ml-2"
        >
          {{ activeFilterCount }}
        </UBadge>
      </UButton>

      <div class="flex items-center gap-2">
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {{ totalResults }} results
        </span>
        <USelect
          v-model="sortBy"
          :options="sortOptions"
          size="sm"
          class="w-32"
        />
      </div>
    </div>

    <UCollapse v-model="showAdvancedFilters">
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-4">
        <div class="space-y-2">
          <C8Label>Content Type</C8Label>
          <div class="flex flex-wrap gap-2">
            <UButton
              v-for="type in contentTypes"
              :key="type.value"
              :variant="filters.contentTypes.includes(type.value) ? 'solid' : 'outline'"
              :color="filters.contentTypes.includes(type.value) ? 'blue' : 'gray'"
              size="sm"
              @click="toggleContentType(type.value)"
            >
              {{ type.label }}
            </UButton>
          </div>
        </div>

        <div class="space-y-2">
          <C8Label>State</C8Label>
          <div class="flex flex-wrap gap-2">
            <UButton
              v-for="state in stateOptions"
              :key="state.value"
              :variant="filters.state === state.value ? 'solid' : 'outline'"
              :color="filters.state === state.value ? 'blue' : 'gray'"
              size="sm"
              @click="filters.state = state.value"
            >
              {{ state.label }}
            </UButton>
          </div>
        </div>

        <div class="space-y-2">
          <C8Label for="author">Author</C8Label>
          <UInput
            id="author"
            v-model="filters.author"
            placeholder="Filter by author..."
            size="sm"
          />
        </div>

        <div class="space-y-2">
          <C8Label>Labels</C8Label>
          <div class="flex gap-2">
            <UInput
              v-model="labelInput"
              placeholder="Add label..."
              size="sm"
              @keyup.enter="addLabel"
            />
            <UButton
              icon="i-heroicons-plus-16-solid"
              variant="outline"
              size="sm"
              @click="addLabel"
            >
              Add
            </UButton>
          </div>
          <div class="flex flex-wrap gap-2">
            <UBadge
              v-for="label in filters.labels"
              :key="label"
              color="blue"
              variant="soft"
              class="cursor-pointer"
              @click="removeLabel(label)"
            >
              {{ label }}
              <UIcon name="i-heroicons-x-mark-16-solid" class="ml-1" />
            </UBadge>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <C8Label for="date-from">From</C8Label>
            <UInput
              id="date-from"
              v-model="filters.dateFrom"
              type="date"
              size="sm"
            />
          </div>
          <div class="space-y-2">
            <C8Label for="date-to">To</C8Label>
            <UInput
              id="date-to"
              v-model="filters.dateTo"
              type="date"
              size="sm"
            />
          </div>
        </div>

        <div v-if="repositories.length > 1" class="space-y-2">
          <C8Label>Repository</C8Label>
          <USelect
            v-model="filters.repository"
            :options="repositoryOptions"
            placeholder="All repositories"
            size="sm"
            clearable
          />
        </div>

        <div class="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
          <UButton
            variant="ghost"
            color="gray"
            size="sm"
            @click="resetFilters"
          >
            Reset All
          </UButton>
          <UButton
            size="sm"
            @click="applyFilters"
          >
            Apply Filters
          </UButton>
        </div>
      </div>
    </UCollapse>

    <div v-if="hasActiveFilters" class="flex flex-wrap gap-2">
      <UBadge
        v-for="(value, key) in activeFiltersDisplay"
        :key="key"
        color="blue"
        variant="soft"
        class="cursor-pointer"
        @click="removeFilter(key)"
      >
        {{ key }}: {{ value }}
        <UIcon name="i-heroicons-x-mark-16-solid" class="ml-1" />
      </UBadge>
    </div>

    <div v-if="showSuggestions && suggestions.length > 0" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-2">
      <div class="space-y-1">
        <div
          v-for="suggestion in suggestions"
          :key="suggestion.text"
          class="flex items-center gap-2 p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
          @click="selectSuggestion(suggestion)"
        >
          <UIcon :name="suggestion.icon" class="text-gray-400" />
          <span class="text-sm">{{ suggestion.text }}</span>
          <UBadge
            :color="suggestion.type === 'issue' ? 'green' : suggestion.type === 'pr' ? 'blue' : 'purple'"
            variant="soft"
            size="xs"
          >
            {{ suggestion.type }}
          </UBadge>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  repositories?: Array<{
    id: number
    full_name: string
  }>
  showSuggestions?: boolean
  totalResults?: number
}

const props = withDefaults(defineProps<Props>(), {
  repositories: () => [],
  showSuggestions: false,
  totalResults: 0
})

const emit = defineEmits<{
  search: [query: string, filters: GitHubFilters]
  filterChange: [filters: GitHubFilters]
  clear: []
}>()

interface GitHubFilters {
  contentTypes: string[]
  state: string
  author: string
  labels: string[]
  dateFrom: string
  dateTo: string
  repository: string | null
}

const searchQuery = ref('')
const showAdvancedFilters = ref(false)
const labelInput = ref('')
const sortBy = ref('relevance')

const filters = ref<GitHubFilters>({
  contentTypes: ['issues', 'prs', 'discussions'],
  state: 'all',
  author: '',
  labels: [],
  dateFrom: '',
  dateTo: '',
  repository: null
})

const contentTypes = [
  { value: 'issues', label: 'Issues' },
  { value: 'prs', label: 'Pull Requests' },
  { value: 'discussions', label: 'Discussions' },
  { value: 'wiki', label: 'Wiki Pages' },
  { value: 'files', label: 'Repository Files' }
]

const stateOptions = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
  { value: 'merged', label: 'Merged' }
]

const sortOptions = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
  { value: 'updated', label: 'Recently Updated' },
  { value: 'comments', label: 'Most Comments' }
]

const suggestions = ref([
  { text: 'authentication bug', type: 'issue', icon: 'i-heroicons-chat-bubble-left-right-16-solid' },
  { text: 'user login flow', type: 'pr', icon: 'i-heroicons-code-bracket-square-16-solid' },
  { text: 'API documentation', type: 'discussion', icon: 'i-heroicons-chat-bubble-left-16-solid' }
])

const repositoryOptions = computed(() => [
  { value: null, label: 'All repositories' },
  ...props.repositories.map(repo => ({
    value: repo.id.toString(),
    label: repo.full_name
  }))
])

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.contentTypes.length < contentTypes.length) count++
  if (filters.value.state !== 'all') count++
  if (filters.value.author) count++
  if (filters.value.labels.length > 0) count++
  if (filters.value.dateFrom) count++
  if (filters.value.dateTo) count++
  if (filters.value.repository) count++
  return count
})

const hasActiveFilters = computed(() => activeFilterCount.value > 0)

const activeFiltersDisplay = computed(() => {
  const display: Record<string, string> = {}

  if (filters.value.contentTypes.length < contentTypes.length) {
    display['Content'] = filters.value.contentTypes.join(', ')
  }
  if (filters.value.state !== 'all') {
    display['State'] = filters.value.state
  }
  if (filters.value.author) {
    display['Author'] = filters.value.author
  }
  if (filters.value.labels.length > 0) {
    display['Labels'] = filters.value.labels.join(', ')
  }
  if (filters.value.dateFrom) {
    display['From'] = filters.value.dateFrom
  }
  if (filters.value.dateTo) {
    display['To'] = filters.value.dateTo
  }
  if (filters.value.repository) {
    const repo = props.repositories.find(r => r.id.toString() === filters.value.repository)
    display['Repository'] = repo?.full_name || filters.value.repository
  }

  return display
})

const performSearch = () => {
  emit('search', searchQuery.value, filters.value)
}

const clearSearch = () => {
  searchQuery.value = ''
  emit('clear')
}

const toggleContentType = (type: string) => {
  const index = filters.value.contentTypes.indexOf(type)
  if (index > -1) {
    filters.value.contentTypes.splice(index, 1)
  } else {
    filters.value.contentTypes.push(type)
  }
}

const addLabel = () => {
  const label = labelInput.value.trim()
  if (label && !filters.value.labels.includes(label)) {
    filters.value.labels.push(label)
    labelInput.value = ''
  }
}

const removeLabel = (label: string) => {
  const index = filters.value.labels.indexOf(label)
  if (index > -1) {
    filters.value.labels.splice(index, 1)
  }
}

const removeFilter = (key: string) => {
  switch (key) {
    case 'Content':
      filters.value.contentTypes = ['issues', 'prs', 'discussions']
      break
    case 'State':
      filters.value.state = 'all'
      break
    case 'Author':
      filters.value.author = ''
      break
    case 'Labels':
      filters.value.labels = []
      break
    case 'From':
      filters.value.dateFrom = ''
      break
    case 'To':
      filters.value.dateTo = ''
      break
    case 'Repository':
      filters.value.repository = null
      break
  }
}

const resetFilters = () => {
  filters.value = {
    contentTypes: ['issues', 'prs', 'discussions'],
    state: 'all',
    author: '',
    labels: [],
    dateFrom: '',
    dateTo: '',
    repository: null
  }
}

const applyFilters = () => {
  emit('filterChange', filters.value)
  showAdvancedFilters.value = false
}

const selectSuggestion = (suggestion: any) => {
  searchQuery.value = suggestion.text
  performSearch()
}

watch(searchQuery, (newQuery) => {
  if (newQuery.length > 2) {
    // Debounced search
    debounceSearch()
  }
})

watch(sortBy, () => {
  emit('filterChange', filters.value)
})

const debounceSearch = debounce(() => {
  performSearch()
}, 300)
</script>
