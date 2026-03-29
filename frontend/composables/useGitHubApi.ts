import { useHttpClient } from './useHttpClient'
import type {
  GitHubRepository,
  GitHubIssue,
  GitHubPullRequest,
  GitHubIngestionRequest,
  GitHubRepositoryResponse,
  GitHubIssuesResponse,
  GitHubPullRequestsResponse
} from '~/types/github'

export const useGitHubApi = () => {
  const { httpGet, httpPost, httpDelete } = useHttpClient()

  const ingestRepository = async (data: GitHubIngestionRequest) => {
    return httpPost<GitHubRepository>('/github-ingestion/ingest-repository/', data as any)
  }

  const getRepositories = async (applicationUuid: string) => {
    return httpGet<GitHubRepositoryResponse[]>('/github-ingestion/repositories/', { application_uuid: applicationUuid }, true)
  }

  const deleteRepository = async (repositoryId: number) => {
    return httpDelete(`/github-ingestion/${repositoryId}/delete/`)
  }

  const reIngestRepository = async (repositoryId: number, since?: string) => {
    const params = since ? { since } : {}
    return httpPost<GitHubRepository>(`/github-ingestion/${repositoryId}/re-ingest/`, {}, params as any)
  }

  const getIssues = async (repositoryId: number, state: 'open' | 'closed' | 'all' = 'all') => {
    return httpGet<GitHubIssuesResponse>(`/github-ingestion/${repositoryId}/issues/`, { state }, true)
  }

  const getPullRequests = async (repositoryId: number, state: 'open' | 'closed' | 'merged' | 'all' = 'all') => {
    return httpGet<GitHubPullRequestsResponse>(`/github-ingestion/${repositoryId}/pull-requests/`, { state }, true)
  }

  const getRateLimitStatus = async () => {
    try {
      return httpGet('/github-ingestion/rate-limit-status/')
    } catch (error) {
      console.warn('Rate limit status not available')
      return null
    }
  }

  return {
    ingestRepository,
    getRepositories,
    deleteRepository,
    reIngestRepository,

    getIssues,
    getPullRequests,

    getRateLimitStatus
  }
}
