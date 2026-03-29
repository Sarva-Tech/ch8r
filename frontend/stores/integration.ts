import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type { PaginatedResponse } from '~/lib/types'

export interface Integration {
  uuid: string
  name: string | null
  provider: string
  supported_types: string[]
  metadata?: {
    account?: {
      login: string
      name: string | null
      avatar_url: string
      html_url: string
    }
    [key: string]: unknown
  } | null
  creator: number
  created_at: string
  updated_at: string
}

export interface SupportedIntegration {
  id: string
  label: string
  description: string
  supported_types: string[]
  credential_fields: string[]
}

export interface IntegrationsResponse extends PaginatedResponse<Integration> {
  supported_integrations: SupportedIntegration[]
}

export interface RepoOption {
  full_name: string
  private: boolean
}

export const useIntegrationStore = defineStore('integration', {
  state: () => ({
    integrations: [] as Integration[],
    supportedIntegrations: [] as SupportedIntegration[],
    // Cache: integrationUuid -> { repos, fetchedAt }
    _reposCache: {} as Record<string, { repos: RepoOption[], fetchedAt: number }>,
  }),

  actions: {
    async load() {
      const { httpGet } = useHttpClient()
      const response = await httpGet<IntegrationsResponse>('/integrations/')
      this.integrations = response.results
      this.supportedIntegrations = response.supported_integrations
      return response
    },

    async create(values: Record<string, unknown>) {
      const { httpPost } = useHttpClient()
      const response = await httpPost<Integration>('/integrations/', values)
      this.integrations = [...this.integrations, response]
      return response
    },

    async update(values: Record<string, unknown>) {
      const { httpPatch } = useHttpClient()
      const response = await httpPatch<Integration>(`/integrations/${values.uuid}/`, values)
      const index = this.integrations.findIndex(i => i.uuid === values.uuid)
      if (index !== -1) {
        this.integrations[index] = { ...this.integrations[index], ...response }
      }
      delete this._reposCache[values.uuid as string]
      return response
    },

    async delete(uuid: string) {
      const { httpDelete } = useHttpClient()
      const response = await httpDelete<{ detail: string }>(`/integrations/${uuid}/`)
      if (response?.detail === 'deleted') {
        this.integrations = this.integrations.filter(i => i.uuid !== uuid)
        delete this._reposCache[uuid]
      }
      return response
    },

    async fetchRepos(integrationUuid: string, forceRefresh = false): Promise<RepoOption[]> {
      const TTL_MS = 5 * 60 * 1000
      const cached = this._reposCache[integrationUuid]
      if (!forceRefresh && cached && Date.now() - cached.fetchedAt < TTL_MS) {
        return cached.repos
      }
      const { httpGet } = useHttpClient()
      const response = await httpGet<{ repos: RepoOption[] }>(`/integrations/${integrationUuid}/repos/`)
      this._reposCache[integrationUuid] = { repos: response.repos, fetchedAt: Date.now() }
      return response.repos
    },
  },
})
