import type {
  ChatResponse,
  CollectionListResponse,
  CollectionSummary,
  ConversationContextMessage,
  DocumentListResponse,
  DocumentRecord,
  IndexResetResponse,
  IndexStatusResponse,
  PublicConfig,
  RuntimeConfig,
  RuntimeOptions,
  RuntimeTestResponse,
} from './types'
import type { ChatRequest } from './api/generated'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function fetchApi(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`Could not reach the local API at ${API_URL}. Start the backend and try again.`)
    }
    throw error
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const errorBody = (await response.json()) as { detail?: unknown }
      if (typeof errorBody.detail === 'string') detail = errorBody.detail
    } catch {
      // Preserve default message when body is not JSON.
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

export async function getConfig(): Promise<PublicConfig> {
  return parseJsonResponse<PublicConfig>(await fetchApi(`${API_URL}/api/config`))
}

export async function getRuntimeConfig(): Promise<RuntimeConfig> {
  return parseJsonResponse<RuntimeConfig>(await fetchApi(`${API_URL}/api/runtime`))
}

export async function testRuntime(runtimeOptions: RuntimeOptions): Promise<RuntimeTestResponse> {
  const response = await fetchApi(`${API_URL}/api/runtime/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: 'Responda apenas: ok', runtime_options: runtimeOptions }),
  })
  return parseJsonResponse<RuntimeTestResponse>(response)
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const body = await parseJsonResponse<DocumentListResponse>(await fetchApi(`${API_URL}/api/documents`))
  return body.documents
}

export async function getCollections(): Promise<CollectionSummary[]> {
  const body = await parseJsonResponse<CollectionListResponse>(await fetchApi(`${API_URL}/api/collections`))
  return body.collections
}

export async function getIndexStatus(): Promise<IndexStatusResponse> {
  return parseJsonResponse<IndexStatusResponse>(await fetchApi(`${API_URL}/api/index/status`))
}

export async function resetIndex(): Promise<IndexResetResponse> {
  return parseJsonResponse<IndexResetResponse>(await fetchApi(`${API_URL}/api/index`, { method: 'DELETE' }))
}

export async function createDocument(input: { title: string; content: string }): Promise<DocumentRecord> {
  const response = await fetchApi(`${API_URL}/api/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...input, source_type: 'manual' }),
  })
  return parseJsonResponse<DocumentRecord>(response)
}

export async function uploadDocument(file: File, title?: string): Promise<DocumentRecord> {
  const formData = new FormData()
  formData.append('file', file)
  if (title) formData.append('title', title)
  return parseJsonResponse<DocumentRecord>(await fetchApi(`${API_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  }))
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetchApi(`${API_URL}/api/documents/${documentId}`, { method: 'DELETE' })
  if (!response.ok) throw new Error(`Could not delete document ${documentId}`)
}

export async function clearChatHistory(): Promise<void> {
  await parseJsonResponse<{ messages_deleted: number }>(await fetchApi(`${API_URL}/api/chat/history`, { method: 'DELETE' }))
}

export async function askQuestion(
  question: string,
  conversationContext: ConversationContextMessage[] = [],
  runtimeOptions?: RuntimeOptions,
  topK?: number,
  collectionId?: string | null,
): Promise<ChatResponse> {
  const body: ChatRequest = {
    question,
    conversation_context: conversationContext,
    runtime_options: runtimeOptions,
    top_k: topK,
    collection_id: collectionId,
  }
  const response = await fetchApi(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJsonResponse<ChatResponse>(response)
}
