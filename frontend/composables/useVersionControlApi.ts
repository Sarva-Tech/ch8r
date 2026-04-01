import { useHttpClient } from './useHttpClient'
import type {
  VCRepository,
  VCIssue,
  VCPullRequest,
  VCIngestionRequest,
  VCRepositoryDetail,
  VCIssuesResponse,
  VCPullRequestsResponse,
  VCProvider
} from '~/types/version_control'

export const useVersionControlApi = () => {
  const { httpGet, httpPost, httpDelete } = useHttpClient()

  const ingestRepository = async (data: VCIngestionRequest) => {
    return httpPost<VCRepository>('/vc-ingestion/ingest-repository/', data as any)
  }

  const getRepositories = async (appIntegrationId?: string) => {
    const params = appIntegrationId ? `?app_integration_id=${appIntegrationId}` : ''
    return httpGet<VCRepository[]>(`/vc-ingestion/repositories/${params}`)
  }

  const deleteRepository = async (repositoryId: string) => {
    return httpDelete(`/vc-ingestion/repositories/${repositoryId}/`)
  }

  const reIngestRepository = async (repositoryId: string, provider?: VCProvider) => {
    const body = provider ? { provider } : {}
    return httpPost<VCRepository>(`/vc-ingestion/repositories/${repositoryId}/re-ingest/`, body)
  }

  const getIssues = async (repositoryId: string, params?: { state?: string; since?: string }) => {
    const queryParams = new URLSearchParams()
    if (params?.state) queryParams.append('state', params.state)
    if (params?.since) queryParams.append('since', params.since)
    const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
    return httpGet<VCIssuesResponse>(`/vc-ingestion/repositories/${repositoryId}/issues/${query}`)
  }

  const getPullRequests = async (repositoryId: string, params?: { state?: string; since?: string }) => {
    const queryParams = new URLSearchParams()
    if (params?.state) queryParams.append('state', params.state)
    if (params?.since) queryParams.append('since', params.since)
    const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
    return httpGet<VCPullRequestsResponse>(`/vc-ingestion/repositories/${repositoryId}/pull-requests/${query}`)
  }

  const getRepositoryDetail = async (repositoryId: string) => {
    return httpGet<VCRepositoryDetail>(`/vc-ingestion/repositories/${repositoryId}/`)
  }

  return {
    ingestRepository,
    getRepositories,
    deleteRepository,
    reIngestRepository,
    getIssues,
    getPullRequests,
    getRepositoryDetail
  }
}
