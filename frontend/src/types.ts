export type RuntimeProfileName = 'economy' | 'balanced' | 'strong' | 'custom'

export type RuntimeOptions = {
  profile?: RuntimeProfileName | null
  model?: string | null
  num_ctx?: number | null
  num_gpu?: number | null
  keep_alive?: string | null
  temperature?: number | null
  think?: boolean | null
  num_predict?: number | null
}

export type RuntimeConfig = {
  llm_provider: string
  llm_model: string
  embedding_provider: string
  embedding_model: string
  default_options: RuntimeOptions
  profiles: Record<string, RuntimeOptions>
}

export type RuntimeTestResponse = {
  success: boolean
  provider: string
  model: string
  latency_ms: number
  answer?: string | null
  error?: string | null
  diagnostics?: components['schemas']['GenerationDiagnostics'] | null
}

export type PublicConfig = {
  app_name: string
  llm_provider: string
  llm_model: string
  embedding_provider: string
  embedding_model: string
  retrieval_top_k: number
  retrieval_min_score: number
  chunk_size: number
  chunk_overlap: number
}

export type DocumentRecord = {
  id: string
  title: string
  source_type: string
  total_chars: number
  total_chunks: number
  created_at: string
  updated_at: string
}

import type {
  ChatResponse as GeneratedChatResponse,
  ConversationMessage as GeneratedConversationMessage,
  SourceChunk as GeneratedSourceChunk,
} from './api/generated'
import type { components } from './generated/openapi'

export type GeneratedChatResponseContract = GeneratedChatResponse
export type GeneratedSourceChunkContract = GeneratedSourceChunk

export type DocumentListResponse = {
  documents: DocumentRecord[]
}

export type CollectionSummary = {
  id: string
  name: string
  kind: 'manual' | 'folder'
  missing_policy: 'mark' | 'remove'
  active_sources: number
  missing_sources: number
  error_sources: number
  last_scanned_at?: string | null
}

export type CollectionListResponse = {
  collections: CollectionSummary[]
}

export type IndexStatusResponse = {
  state: 'empty' | 'ready' | 'legacy' | 'incompatible'
  configured_provider: string
  configured_model: string
  stored_provider?: string | null
  stored_model?: string | null
  stored_dimension?: number | null
  document_count: number
  chunk_count: number
  reindex_required: boolean
  reason?: string | null
}

export type IndexResetResponse = {
  documents_deleted: number
  chunks_deleted: number
}

export type SourceChunk = GeneratedSourceChunk
export type ChatDiagnostics = components['schemas']['ChatDiagnostics']
export type GenerationDiagnostics = components['schemas']['GenerationDiagnostics']

export type ConversationContextMessage = GeneratedConversationMessage

export type ChatResponse = GeneratedChatResponse
