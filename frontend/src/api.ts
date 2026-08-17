import type {
  ChatResponse,
  ConversationContextMessage,
  DocumentListResponse,
  DocumentRecord,
  PublicConfig,
  RuntimeConfig,
  RuntimeOptions,
  RuntimeTestResponse,
} from './types'

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

export async function getRuntimeConfig(): Promise<RuntimeConfig> {
  const response = await fetchApi(`${API_URL}/api/runtime`)
  return parseJsonResponse<RuntimeConfig>(response)
}

export async function testRuntime(runtimeOptions: RuntimeOptions): Promise<RuntimeTestResponse> {
  const response = await fetchApi(`${API_URL}/api/runtime/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: 'Responda apenas: ok',
      runtime_options: runtimeOptions,
    }),
  })
  return parseJsonResponse<RuntimeTestResponse>(response)
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

export async function clearChatHistory(): Promise<void> {
  const response = await fetchApi(`${API_URL}/api/chat/history`, {
    method: 'DELETE',
  })
  await parseJsonResponse<{ messages_deleted: number }>(response)
}

export async function askQuestion(
  question: string,
  conversationContextOrRuntime: ConversationContextMessage[] | RuntimeOptions = [],
  runtimeOptionsOrTopK?: RuntimeOptions | number,
  explicitTopK?: number,
): Promise<ChatResponse> {
  const explicitContext = Array.isArray(conversationContextOrRuntime)
  const parsed = explicitContext
    ? { question, context: conversationContextOrRuntime }
    : parseLegacyContextualQuestion(question)
  const runtimeOptions = explicitContext
    ? (typeof runtimeOptionsOrTopK === 'object' ? runtimeOptionsOrTopK : undefined)
    : conversationContextOrRuntime
  const topK = explicitContext
    ? (typeof runtimeOptionsOrTopK === 'number' ? runtimeOptionsOrTopK : explicitTopK)
    : (typeof runtimeOptionsOrTopK === 'number' ? runtimeOptionsOrTopK : undefined)

  const response = await fetchApi(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: parsed.question,
      conversation_context: parsed.context,
      runtime_options: runtimeOptions,
      top_k: topK,
    }),
  })
  return parseJsonResponse<ChatResponse>(response)
}

function parseLegacyContextualQuestion(input: string): {
  question: string
  context: ConversationContextMessage[]
} {
  const markers = [
    {
      contextHeading: 'Recent conversation context:',
      questionHeading: 'Current user question:',
      userPrefix: 'User: ',
      assistantPrefix: 'Assistant: ',
    },
    {
      contextHeading: 'Contexto recente da conversa:',
      questionHeading: 'Pergunta atual do usuário:',
      userPrefix: 'Usuário: ',
      assistantPrefix: 'Assistente: ',
    },
  ]

  for (const marker of markers) {
    const contextStart = input.indexOf(marker.contextHeading)
    const questionStart = input.lastIndexOf(marker.questionHeading)
    if (contextStart !== 0 || questionStart <= marker.contextHeading.length) continue

    const rawContext = input
      .slice(marker.contextHeading.length, questionStart)
      .trim()
    const currentQuestion = input
      .slice(questionStart + marker.questionHeading.length)
      .trim()
    if (!currentQuestion) continue

    const context = rawContext
      .split(/\n\n+/)
      .map((block): ConversationContextMessage | null => {
        if (block.startsWith(marker.userPrefix)) {
          return { role: 'user', content: block.slice(marker.userPrefix.length).trim() }
        }
        if (block.startsWith(marker.assistantPrefix)) {
          return { role: 'assistant', content: block.slice(marker.assistantPrefix.length).trim() }
        }
        return null
      })
      .filter((message): message is ConversationContextMessage =>
        message !== null && message.content.length > 0,
      )
      .slice(-12)

    return { question: currentQuestion, context }
  }

  return { question: input, context: [] }
}
