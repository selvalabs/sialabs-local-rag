export type RuntimeProfileName = 'economy' | 'balanced' | 'strong' | 'custom'

export type RuntimeOptions = {
  profile?: RuntimeProfileName | null
  model?: string | null
  num_ctx?: number | null
  num_gpu?: number | null
  keep_alive?: string | null
  temperature?: number | null
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
}

export type PublicConfig = {
  app_name: string
  llm_provider: string
  llm_model: string
  embedding_provider: string
  embedding_model: string
  retrieval_top_k: number
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

export type DocumentListResponse = {
  documents: DocumentRecord[]
}

export type SourceChunk = {
  chunk_id: string
  document_id: string
  document_title: string
  chunk_index: number
  score: number
  content: string
}

export type ChatResponse = {
  answer: string
  sources: SourceChunk[]
  provider: string
  model: string
  retrieval_top_k: number
  latency_ms: number
}
