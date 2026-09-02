// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { CollectionSummary } from './types'

const api = vi.hoisted(() => ({
  askQuestion: vi.fn(),
  clearChatHistory: vi.fn(),
  createDocument: vi.fn(),
  getCollections: vi.fn(),
  getConfig: vi.fn(),
  getIndexStatus: vi.fn(),
  getRuntimeConfig: vi.fn(),
  resetIndex: vi.fn(),
  testRuntime: vi.fn(),
  uploadDocument: vi.fn(),
}))
const documents = vi.hoisted(() => ({
  refreshDocuments: vi.fn(),
  removeDocument: vi.fn(),
}))

vi.mock('./api', () => api)
vi.mock('./hooks/useDocuments', () => ({
  useDocuments: () => ({ documents: [], ...documents }),
}))

import App from './App'

const defaultCollection: CollectionSummary = {
  id: 'default',
  name: 'Local base',
  kind: 'manual',
  missing_policy: 'mark',
  active_sources: 0,
  missing_sources: 0,
  error_sources: 0,
}

function renderApp(collections: CollectionSummary[] = [defaultCollection]) {
  api.getConfig.mockResolvedValue({
    llm_provider: 'mock',
    llm_model: 'local-mock',
    embedding_provider: 'hash',
    embedding_model: 'hash-bow-128',
    retrieval_top_k: 5,
    retrieval_min_score: 0,
    chunk_size: 1200,
    chunk_overlap: 180,
  })
  api.getRuntimeConfig.mockResolvedValue({
    llm_provider: 'mock',
    llm_model: 'local-mock',
    embedding_provider: 'hash',
    embedding_model: 'hash-bow-128',
    default_options: { profile: 'balanced', think: false },
    profiles: {
      economy: { profile: 'economy', num_ctx: 2048, num_gpu: 0, think: false },
      balanced: { profile: 'balanced', num_ctx: 1024, num_gpu: null, think: false },
      strong: { profile: 'strong', num_ctx: 4096, num_gpu: null, think: true },
    },
  })
  api.getCollections.mockResolvedValue(collections)
  api.getIndexStatus.mockResolvedValue({
    state: 'empty',
    configured_provider: 'hash',
    configured_model: 'hash-bow-128',
    document_count: 0,
    chunk_count: 0,
    reindex_required: false,
  })
  documents.refreshDocuments.mockResolvedValue(undefined)
  render(<App />)
}

beforeEach(() => {
  vi.clearAllMocks()
  window.localStorage.clear()
})

afterEach(cleanup)

describe('local workspace UX states', () => {
  it('does not render a collection selector when only one collection exists', async () => {
    renderApp()

    await waitFor(() => expect(api.getCollections).toHaveBeenCalled())
    expect(screen.queryByLabelText('Collection')).toBeNull()
  })

  it('renders the compact collection selector when multiple collections exist', async () => {
    renderApp([
      defaultCollection,
      { ...defaultCollection, id: 'work', name: 'Work documents', kind: 'folder' },
    ])

    const selector = await screen.findByLabelText('Collection')
    expect(selector.closest('.collection-selector')?.classList.contains('compact')).toBe(true)
    expect(screen.getByRole('option', { name: /work documents/i })).toBeTruthy()
  })

  it('shows selected, uploading, and ready upload states', async () => {
    let resolveUpload: (() => void) | undefined
    api.uploadDocument.mockImplementation(
      () => new Promise<void>((resolve) => { resolveUpload = resolve }),
    )
    renderApp()

    const fileInput = screen.getByLabelText('Choose file')
    fireEvent.change(fileInput, { target: { files: [new File(['local document'], 'notes.txt')] } })
    expect(screen.getByText('Selected — ready to add')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Add file' }))
    expect(screen.getByRole('status').textContent).toBe('Uploading and indexing…')

    resolveUpload?.()
    await waitFor(() => expect(screen.getByText('File indexed and ready')).toBeTruthy())
  })

  it('shows an error state when upload indexing fails', async () => {
    api.uploadDocument.mockRejectedValue(new Error('Indexing unavailable'))
    renderApp()

    fireEvent.change(screen.getByLabelText('Choose file'), {
      target: { files: [new File(['local document'], 'notes.txt')] },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add file' }))

    await waitFor(() => expect(screen.getByText('File could not be indexed')).toBeTruthy())
  })

  it.each([
    ['Economy', false],
    ['Balanced', false],
    ['Strong', true],
  ])('applies thinking %s profile defaults', async (profile, expectedThinking) => {
    renderApp()

    await screen.findByRole('button', { name: profile })
    fireEvent.click(screen.getByRole('button', { name: profile }))

    expect((screen.getByLabelText('Thinking') as HTMLInputElement).checked).toBe(expectedThinking)
  })

  it('uses a custom profile and sends the selected thinking value to the runtime API', async () => {
    api.testRuntime.mockResolvedValue({
      success: true,
      provider: 'mock',
      model: 'local-mock',
      latency_ms: 1,
      answer: 'ok',
      error: null,
    })
    renderApp()

    const thinkingInput = await screen.findByLabelText('Thinking')
    fireEvent.click(thinkingInput)
    expect(screen.getByRole('button', { name: 'Custom' }).classList.contains('active')).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: 'Test local AI' }))
    await waitFor(() =>
      expect(api.testRuntime).toHaveBeenCalledWith(
        expect.objectContaining({ profile: 'custom', think: true }),
      ),
    )
  })
})
