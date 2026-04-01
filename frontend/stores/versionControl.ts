import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  VCRepository,
  VCIssue,
  VCPullRequest,
  VCStats,
  VCFilters,
  VCIngestionRequest,
  VCProvider
} from '~/types/version_control'
import { useVersionControlApi } from '~/composables/useVersionControlApi'

export const useVersionControlStore = defineStore('versionControl', () => {
  const repositories = ref<VCRepository[]>([])
  const currentRepository = ref<VCRepository | null>(null)
  const issues = ref<VCIssue[]>([])
  const pullRequests = ref<VCPullRequest[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const ingestionStatus = ref<'idle' | 'ingesting' | 'completed' | 'failed'>('idle')

  const api = useVersionControlApi()

  const filters = ref<VCFilters>({
    state: 'all',
    author: '',
    labels: [],
    since: '',
    until: '',
    search: ''
  })

  const stats = computed<VCStats>(() => {
    const openIssues = issues.value.filter(i => i.state === 'open').length
    const closedIssues = issues.value.filter(i => i.state === 'closed').length
    const openPRs = pullRequests.value.filter(pr => pr.state === 'open').length
    const mergedPRs = pullRequests.value.filter(pr => pr.state === 'merged').length

    return {
      totalIssues: issues.value.length,
      openIssues,
      closedIssues,
      totalPRs: pullRequests.value.length,
      openPRs,
      mergedPRs
    }
  })

  const filteredIssues = computed(() => {
    let result = issues.value

    if (filters.value.state !== 'all') {
      result = result.filter(i => i.state === filters.value.state)
    }

    if (filters.value.author) {
      result = result.filter(i => i.author === filters.value.author)
    }

    if (filters.value.labels.length > 0) {
      result = result.filter(i =>
        filters.value.labels.some(label => i.labels.includes(label))
      )
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(i =>
        i.title.toLowerCase().includes(search) ||
        i.body.toLowerCase().includes(search)
      )
    }

    return result
  })

  const filteredPullRequests = computed(() => {
    let result = pullRequests.value

    if (filters.value.state !== 'all') {
      result = result.filter(pr => pr.state === filters.value.state)
    }

    if (filters.value.author) {
      result = result.filter(pr => pr.author === filters.value.author)
    }

    if (filters.value.labels.length > 0) {
      result = result.filter(pr =>
        filters.value.labels.some(label => pr.labels.includes(label))
      )
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(pr =>
        pr.title.toLowerCase().includes(search) ||
        pr.body.toLowerCase().includes(search)
      )
    }

    return result
  })

  async function ingestRepository(data: VCIngestionRequest) {
    loading.value = true
    error.value = null
    ingestionStatus.value = 'ingesting'

    try {
      const result = await api.ingestRepository(data)
      if (!repositories.value.find(r => r.uuid === result.uuid)) {
        repositories.value.push(result)
      }
      ingestionStatus.value = 'completed'
      return result
    } catch (e: any) {
      error.value = e.message || 'Failed to ingest repository'
      ingestionStatus.value = 'failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadRepositories(appIntegrationId?: string) {
    loading.value = true
    error.value = null

    try {
      const result = await api.getRepositories(appIntegrationId)
      repositories.value = result
      return result
    } catch (e: any) {
      error.value = e.message || 'Failed to load repositories'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteRepository(repositoryId: string) {
    loading.value = true
    error.value = null

    try {
      await api.deleteRepository(repositoryId)
      repositories.value = repositories.value.filter(r => r.uuid !== repositoryId)
      if (currentRepository.value?.uuid === repositoryId) {
        currentRepository.value = null
      }
    } catch (e: any) {
      error.value = e.message || 'Failed to delete repository'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadIssues(repositoryId: string, params?: { state?: string; since?: string }) {
    loading.value = true
    error.value = null

    try {
      const result = await api.getIssues(repositoryId, params)
      issues.value = result.results
      return result
    } catch (e: any) {
      error.value = e.message || 'Failed to load issues'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadPullRequests(repositoryId: string, params?: { state?: string; since?: string }) {
    loading.value = true
    error.value = null

    try {
      const result = await api.getPullRequests(repositoryId, params)
      pullRequests.value = result.results
      return result
    } catch (e: any) {
      error.value = e.message || 'Failed to load pull requests'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function selectRepository(repository: VCRepository | null) {
    currentRepository.value = repository
    if (repository) {
      await Promise.all([
        loadIssues(repository.uuid),
        loadPullRequests(repository.uuid)
      ])
    } else {
      issues.value = []
      pullRequests.value = []
    }
  }

  function setFilters(newFilters: Partial<VCFilters>) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function clearFilters() {
    filters.value = {
      state: 'all',
      author: '',
      labels: [],
      since: '',
      until: '',
      search: ''
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    repositories,
    currentRepository,
    issues,
    pullRequests,
    loading,
    error,
    ingestionStatus,
    filters,
    stats,
    filteredIssues,
    filteredPullRequests,
    ingestRepository,
    loadRepositories,
    deleteRepository,
    loadIssues,
    loadPullRequests,
    selectRepository,
    setFilters,
    clearFilters,
    clearError
  }
})
