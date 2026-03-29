import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  GitHubRepository,
  GitHubIssue,
  GitHubPullRequest,
  GitHubStats,
  GitHubFilters
} from '~/types/github'
import { useGitHubApi } from '~/composables/useGitHubApi'

export const useGitHubStore = defineStore('github', () => {
  const repositories = ref<GitHubRepository[]>([])
  const currentRepository = ref<GitHubRepository | null>(null)
  const issues = ref<GitHubIssue[]>([])
  const pullRequests = ref<GitHubPullRequest[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const ingestionStatus = ref<'idle' | 'ingesting' | 'completed' | 'failed'>('idle')
  const filters = ref<GitHubFilters>({
    state: 'all',
    author: '',
    labels: [],
    since: '',
    until: '',
    search: ''
  })

  const githubApi = useGitHubApi()

  const stats = computed<GitHubStats>(() => {
    const totalIssues = issues.value.length
    const openIssues = issues.value.filter(issue => issue.state === 'open').length
    const closedIssues = issues.value.filter(issue => issue.state === 'closed').length

    const totalPRs = pullRequests.value.length
    const openPRs = pullRequests.value.filter(pr => pr.state === 'open').length
    const mergedPRs = pullRequests.value.filter(pr => pr.state === 'merged').length

    return {
      totalIssues,
      openIssues,
      closedIssues,
      totalPRs,
      openPRs,
      mergedPRs,
      totalDiscussions: 0,
      totalWikiPages: 0,
      totalFiles: 0
    }
  })

  const filteredIssues = computed(() => {
    let filtered = issues.value

    if (filters.value.state !== 'all') {
      filtered = filtered.filter(issue => issue.state === filters.value.state)
    }

    if (filters.value.author) {
      filtered = filtered.filter(issue =>
        issue.author.toLowerCase().includes(filters.value.author.toLowerCase())
      )
    }

    if (filters.value.labels.length > 0) {
      filtered = filtered.filter(issue =>
        filters.value.labels.some(label => issue.labels.includes(label))
      )
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      filtered = filtered.filter(issue =>
        issue.title.toLowerCase().includes(search) ||
        issue.body.toLowerCase().includes(search)
      )
    }

    return filtered
  })

  const filteredPullRequests = computed(() => {
    let filtered = pullRequests.value

    if (filters.value.state !== 'all') {
      filtered = filtered.filter(pr => pr.state === filters.value.state)
    }

    if (filters.value.author) {
      filtered = filtered.filter(pr =>
        pr.author.toLowerCase().includes(filters.value.author.toLowerCase())
      )
    }

    if (filters.value.labels.length > 0) {
      filtered = filtered.filter(pr =>
        filters.value.labels.some(label => pr.labels.includes(label))
      )
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      filtered = filtered.filter(pr =>
        pr.title.toLowerCase().includes(search) ||
        pr.body.toLowerCase().includes(search)
      )
    }

    return filtered
  })

  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const setError = (value: string | null) => {
    error.value = value
  }

  const setIngestionStatus = (value: 'idle' | 'ingesting' | 'completed' | 'failed') => {
    ingestionStatus.value = value
  }

  const setCurrentRepository = (repository: GitHubRepository | null) => {
    currentRepository.value = repository
  }

  const updateFilters = (newFilters: Partial<GitHubFilters>) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const resetFilters = () => {
    filters.value = {
      state: 'all',
      author: '',
      labels: [],
      since: '',
      until: '',
      search: ''
    }
  }

  const ingestRepository = async (data: { owner: string; repo: string; application_uuid: string; since?: string }) => {
    try {
      setLoading(true)
      setError(null)
      setIngestionStatus('ingesting')

      await githubApi.ingestRepository(data)

      setIngestionStatus('ingesting')
    } catch (err: any) {
      setError(err.message || 'Failed to ingest repository')
      setIngestionStatus('failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const fetchRepositories = async (applicationUuid: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await githubApi.getRepositories(applicationUuid)
      repositories.value = response

      return response
    } catch (err: any) {
      setError(err.message || 'Failed to fetch repositories')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const deleteRepository = async (repositoryId: number) => {
    try {
      setLoading(true)
      setError(null)

      await githubApi.deleteRepository(repositoryId)

      repositories.value = repositories.value.filter(repo => repo.id !== repositoryId)

      if (currentRepository.value?.id === repositoryId) {
        currentRepository.value = null
        issues.value = []
        pullRequests.value = []
      }

    } catch (err: any) {
      setError(err.message || 'Failed to delete repository')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const reIngestRepository = async (repositoryId: number, since?: string) => {
    try {
      setLoading(true)
      setError(null)
      setIngestionStatus('ingesting')

      const response = await githubApi.reIngestRepository(repositoryId, since)

      const index = repositories.value.findIndex(repo => repo.id === repositoryId)
      if (index !== -1) {
        repositories.value[index] = response
      }

      setIngestionStatus('completed')

      return response
    } catch (err: any) {
      setError(err.message || 'Failed to re-ingest repository')
      setIngestionStatus('failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const fetchIssues = async (repositoryId: number, state: 'all' | 'open' | 'closed' = 'all') => {
    try {
      setLoading(true)
      setError(null)

      const response = await githubApi.getIssues(repositoryId, state)
      issues.value = response.results || response // Handle both paginated and direct response

      return response
    } catch (err: any) {
      setError(err.message || 'Failed to fetch issues')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const fetchPullRequests = async (repositoryId: number, state: 'all' | 'open' | 'closed' | 'merged' = 'all') => {
    try {
      setLoading(true)
      setError(null)

      const response = await githubApi.getPullRequests(repositoryId, state)
      pullRequests.value = response.results || response // Handle both paginated and direct response

      return response
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pull requests')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const getRepositoryByFullName = (fullName: string) => {
    return repositories.value.find(repo => repo.full_name === fullName)
  }

  const getRepositoryById = (id: number) => {
    return repositories.value.find(repo => repo.id === id)
  }

  const clearData = () => {
    repositories.value = []
    currentRepository.value = null
    issues.value = []
    pullRequests.value = []
    error.value = null
    ingestionStatus.value = 'idle'
    resetFilters()
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

    setLoading,
    setError,
    setIngestionStatus,
    setCurrentRepository,
    updateFilters,
    resetFilters,

    fetchRepositories,
    ingestRepository,
    deleteRepository,
    reIngestRepository,

    fetchIssues,
    fetchPullRequests,

    getRepositoryByFullName,
    getRepositoryById,
    clearData
  }
})
