export type VCProvider = 'github_graphql'

export interface VCRepository {
  id: number
  uuid: string
  provider: VCProvider
  external_id: string
  name: string
  repo_owner: string
  full_name: string
  description: string
  url: string
  is_private: boolean
  default_branch: string
  last_ingested_at: string | null
  ingestion_status: 'pending' | 'running' | 'completed' | 'failed'
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface VCIssue {
  id: number
  uuid: string
  external_id: string
  number: number
  title: string
  body: string
  state: 'open' | 'closed'
  author: string
  author_association: string
  assignees: string[]
  labels: string[]
  milestone: any
  locked: boolean
  created_at: string
  updated_at: string
  closed_at: string | null
  url: string
  repository: string
  comments: VCIssueComment[]
  comment_count: number
}

export interface VCIssueComment {
  id: number
  uuid: string
  external_id: string
  body: string
  author: string
  author_association: string
  created_at: string
  updated_at: string
  url: string
}

export interface VCPullRequest {
  id: number
  uuid: string
  external_id: string
  number: number
  title: string
  body: string
  state: 'open' | 'closed' | 'merged'
  author: string
  author_association: string
  assignees: string[]
  reviewers: string[]
  labels: string[]
  milestone: any
  head_branch: string
  base_branch: string
  merged: boolean
  merged_at: string | null
  merge_commit_sha: string
  additions: number
  deletions: number
  changed_files: number
  created_at: string
  updated_at: string
  closed_at: string | null
  url: string
  repository: string
  comments: VCPRComment[]
  files: VCPRFile[]
  comment_count: number
  file_count: number
}

export interface VCPRComment {
  id: number
  uuid: string
  external_id: string
  body: string
  author: string
  author_association: string
  created_at: string
  updated_at: string
  url: string
}

export interface VCPRFile {
  id: number
  uuid: string
  filename: string
  status: 'added' | 'modified' | 'removed' | 'renamed'
  additions: number
  deletions: number
  changes: number
  patch: string
  blob_url: string
  raw_url: string
  contents_url: string
}

export interface VCIngestionRequest {
  owner: string
  repo: string
  since?: string
  application_uuid: string
  provider?: VCProvider
}

export interface VCRepositoryDetail extends VCRepository {
  issue_count: number
  pr_count: number
}

export interface VCIssuesResponse {
  count: number
  next: string | null
  previous: string | null
  results: VCIssue[]
}

export interface VCPullRequestsResponse {
  count: number
  next: string | null
  previous: string | null
  results: VCPullRequest[]
}

export interface VCIngestionStatus {
  status: 'success' | 'error' | 'pending'
  repository: string
  message: string
  completed_at?: string
  error?: string
}

export interface VCState {
  repositories: VCRepository[]
  currentRepository: VCRepository | null
  issues: VCIssue[]
  pullRequests: VCPullRequest[]
  loading: boolean
  error: string | null
  ingestionStatus: 'idle' | 'ingesting' | 'completed' | 'failed'
}

export interface VCFilters {
  state: 'all' | 'open' | 'closed' | 'merged'
  author: string
  labels: string[]
  since: string
  until: string
  search: string
}

export interface VCStats {
  totalIssues: number
  openIssues: number
  closedIssues: number
  totalPRs: number
  openPRs: number
  mergedPRs: number
}
