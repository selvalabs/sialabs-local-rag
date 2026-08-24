import { afterEach, describe, expect, it, vi } from 'vitest'

import { askQuestion, getConfig } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('API client', () => {
  it('parses the public configuration response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          app_name: 'Local RAG',
          llm_provider: 'mock',
          llm_model: 'local-mock',
          embedding_provider: 'hash',
          embedding_model: 'hash-bow-128',
          retrieval_top_k: 5,
          retrieval_min_score: 0,
          chunk_size: 1200,
          chunk_overlap: 180,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getConfig()).resolves.toMatchObject({ llm_provider: 'mock' })
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/config', undefined)
  })

  it('sends typed chat fields in the request body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          answer: 'Local answer',
          sources: [],
          provider: 'mock',
          model: 'local-mock',
          retrieval_query: 'question',
          retrieval_top_k: 5,
          latency_ms: 1,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await askQuestion('question', [{ role: 'user', content: 'previous' }], { profile: 'balanced' })

    const request = fetchMock.mock.calls[0][1] as RequestInit
    expect(JSON.parse(String(request.body))).toMatchObject({
      question: 'question',
      conversation_context: [{ role: 'user', content: 'previous' }],
      runtime_options: { profile: 'balanced' },
    })
  })
})
