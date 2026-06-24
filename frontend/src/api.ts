import type { ChatResponse, DocumentListResponse, DocumentRecord, PublicConfig } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function fetchApi(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Could not reach the local API at ${API_URL}. Start the backend and try again.`,
      )
    }
    throw error
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const errorBody = (await response.json()) as { detail?: unknown }
      if (typeof errorBody.detail === 'string') {
        detail = errorBody.detail
      }
    } catch {
      // Preserve default message when body is not JSON.
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

export async function getConfig(): Promise<PublicConfig> {
  const response = await fetchApi(`${API_URL}/api/config`)
  return parseJsonResponse<PublicConfig>(response)
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await fetchApi(`${API_URL}/api/documents`)
  const body = await parseJsonResponse<DocumentListResponse>(response)
  return body.documents
}

export async function createDocument(input: {
  title: string
  content: string
}): Promise<DocumentRecord> {
  const response = await fetchApi(`${API_URL}/api/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: input.title,
      content: input.content,
      source_type: 'manual',
    }),
  })
  return parseJsonResponse<DocumentRecord>(response)
}

export async function uploadDocument(file: File, title?: string): Promise<DocumentRecord> {
  const formData = new FormData()
  formData.append('file', file)
  if (title) {
    formData.append('title', title)
  }

  const response = await fetchApi(`${API_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  return parseJsonResponse<DocumentRecord>(response)
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetchApi(`${API_URL}/api/documents/${documentId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Could not delete document ${documentId}`)
  }
}

export async function askQuestion(question: string): Promise<ChatResponse> {
  const response = await fetchApi(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  return parseJsonResponse<ChatResponse>(response)
}
