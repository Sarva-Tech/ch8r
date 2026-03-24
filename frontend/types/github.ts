export interface GitHubRepository {
  id: number
  uuid: string
  name: string
  owner: string
  full_name: string
  description: string
  url: string
  is_private: boolean
  default_branch: string
  last_ingested_at: string | null
  ingestion_status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

export interface GitHubIssue {
  id: number
  uuid: string
  github_id: number
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
  comments: GitHubIssueComment[]
  comment_count: number
}

export interface GitHubIssueComment {
  id: number
  uuid: string
  github_id: number
  body: string
  author: string
  author_association: string
  created_at: string
  updated_at: string
  url: string
}

export interface GitHubPullRequest {
  id: number
  uuid: string
  github_id: number
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
  comments: GitHubPRComment[]
  files: GitHubPRFile[]
  comment_count: number
  file_count: number
}

export interface GitHubPRComment {
  id: number
  uuid: string
  github_id: number
  body: string
  author: string
  author_association: string
  created_at: string
  updated_at: string
  url: string
}

export interface GitHubPRFile {
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

export interface GitHubDiscussion {
  id: number
  uuid: string
  github_id: number
  number: number
  title: string
  body: string
  author: string
  author_association: string
  category: {
    id: number
    name: string
    emoji: string
    description: string
  }
  answer_chosen_at: string | null
  answer_chosen_by: string
  upvote_count: number
  viewer_has_upvoted: boolean
  created_at: string
  updated_at: string
  last_edited_at: string | null
  url: string
  comments: GitHubDiscussionComment[]
  comment_count: number
}

export interface GitHubDiscussionComment {
  id: number
  uuid: string
  github_id: number
  body: string
  author: string
  author_association: string
  created_at: string
  updated_at: string
  last_edited_at: string | null
  upvote_count: number
  viewer_has_upvoted: boolean
  parent_comment: number | null
  replies: GitHubDiscussionComment[]
}

export interface GitHubWikiPage {
  id: number
  uuid: string
  title: string
  content: string
  sha: string
  html_url: string
  download_url: string
  last_modified: string
}

export interface GitHubRepositoryFile {
  id: number
  uuid: string
  path: string
  name: string
  content: string
  sha: string
  size: number
  content_type: string
  encoding: string
  html_url: string
  download_url: string
  last_modified: string
}

export interface GitHubIngestionRequest {
  owner: string
  repo: string
  since?: string
  app_integration_id: number
}

export interface GitHubRepositoryResponse extends GitHubRepository {
  issue_count: number
  pr_count: number
  discussion_count: number
  wiki_page_count: number
  file_count: number
}

export interface GitHubIssuesResponse {
  count: number
  next: string | null
  previous: string | null
  results: GitHubIssue[]
}

export interface GitHubPullRequestsResponse {
  count: number
  next: string | null
  previous: string | null
  results: GitHubPullRequest[]
}

export interface GitHubIngestionStatus {
  status: 'success' | 'error' | 'pending'
  repository: string
  message: string
  completed_at?: string
  error?: string
}

export interface GitHubIngestionState {
  repositories: GitHubRepository[]
  currentRepository: GitHubRepository | null
  issues: GitHubIssue[]
  pullRequests: GitHubPullRequest[]
  loading: boolean
  error: string | null
  ingestionStatus: 'idle' | 'ingesting' | 'completed' | 'failed'
}

export interface GitHubFilters {
  state: 'all' | 'open' | 'closed' | 'merged'
  author: string
  labels: string[]
  since: string
  until: string
  search: string
}

export interface GitHubStats {
  totalIssues: number
  openIssues: number
  closedIssues: number
  totalPRs: number
  openPRs: number
  mergedPRs: number
  totalDiscussions: number
  totalWikiPages: number
  totalFiles: number
}
