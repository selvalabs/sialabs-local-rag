import { expect, test } from '@playwright/test'

const document = {
  id: 'doc-1',
  title: 'E2E handbook',
  source_type: 'manual',
  total_chars: 42,
  total_chunks: 1,
  created_at: '2026-08-24T00:00:00Z',
  updated_at: '2026-08-24T00:00:00Z',
}

test.beforeEach(async ({ page }) => {
  let documents: typeof document[] = []

  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    let body: unknown

    if (url.pathname === '/api/config') {
      body = {
        app_name: 'SIALabs Local RAG',
        llm_provider: 'mock',
        llm_model: 'mock-chat',
        embedding_provider: 'hash',
        embedding_model: 'hash-bow-128',
        retrieval_top_k: 3,
        retrieval_min_score: 0.25,
        chunk_size: 800,
        chunk_overlap: 80,
      }
    } else if (url.pathname === '/api/runtime') {
      body = {
        llm_provider: 'mock',
        llm_model: 'mock-chat',
        embedding_provider: 'hash',
        embedding_model: 'hash-bow-128',
        default_options: {},
        profiles: {},
      }
    } else if (url.pathname === '/api/documents' && request.method() === 'GET') {
      body = { documents }
    } else if (url.pathname === '/api/collections') {
      body = { collections: [] }
    } else if (url.pathname === '/api/index/status') {
      body = {
        state: documents.length ? 'ready' : 'empty',
        configured_provider: 'hash',
        configured_model: 'hash-bow-128',
        document_count: documents.length,
        chunk_count: documents.length,
        reindex_required: false,
      }
    } else if (url.pathname === '/api/documents' && request.method() === 'POST') {
      documents = [document]
      body = document
    } else if (url.pathname === '/api/chat' && request.method() === 'POST') {
      body = {
        answer: 'Use the local handbook for the answer.',
        sources: [{
          ...document,
          chunk_id: 'chunk-1',
          document_id: document.id,
          document_title: document.title,
          chunk_index: 0,
          score: 0.91,
          content: 'The local handbook says to use the local workspace.',
          retrieval_channels: ['dense'],
        }],
        provider: 'mock',
        model: 'mock-chat',
        retrieval_query: 'How do I use the handbook?',
        retrieval_top_k: 3,
        retrieval_mode: 'dense',
        latency_ms: 4,
      }
    } else {
      body = {}
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })
})

test('loads the local RAG workspace shell', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Chat with the base' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Send' })).toBeVisible()
})

test('ingests a document and asks a grounded question', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Paste document' }).click()

  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Title').fill('E2E handbook')
  await dialog.getByLabel('Document content').fill('The local handbook says to use the local workspace.')
  await dialog.getByRole('button', { name: 'Add to base' }).click()

  await page.locator('details.base-card > summary').click()
  await expect(page.getByText('E2E handbook')).toBeVisible()
  const question = page.locator('.chat-form textarea')
  await question.fill('How do I use the handbook?')
  await page.getByRole('button', { name: 'Send' }).click()

  await expect(page.getByText('Use the local handbook for the answer.')).toBeVisible()
  await expect(page.getByText('Retrieved sources')).toBeVisible()
  await page.locator('details.sources-block > summary').click()
  await expect(page.getByText('E2E handbook · chunk 0 · dense · score 0.91')).toBeVisible()
})
