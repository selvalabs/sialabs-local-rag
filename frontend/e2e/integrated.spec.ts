import { expect, test } from '@playwright/test'

const API_URL = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000'

test.describe('integrated local RAG flow', () => {
  test.beforeEach(async ({ request }) => {
    const response = await request.delete(`${API_URL}/api/index`)
    expect(response.ok()).toBeTruthy()
  })

  test('React to FastAPI to SQLite to hash retrieval returns a source', async ({ page, request }) => {
    const title = `Playwright integrated ${Date.now()}`
    const evidence = 'The Orion emergency protocol requires code ZEPHYR-17 for response.'

    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Chat with the base' })).toBeVisible()

    await page.getByRole('button', { name: 'Paste document' }).click()
    const dialog = page.getByRole('dialog')
    await dialog.getByLabel('Title').fill(title)
    await dialog.getByLabel('Document content').fill(evidence)
    await dialog.getByRole('button', { name: 'Add to base' }).click()
    await expect(dialog).not.toBeVisible()

    const documentsResponse = await request.get(`${API_URL}/api/documents`)
    expect(documentsResponse.ok()).toBeTruthy()
    expect((await documentsResponse.json()).documents.some((document: { title: string }) => document.title === title)).toBeTruthy()

    await page.locator('details.base-card > summary').click()
    await expect(page.getByText(title)).toBeVisible()

    await page.locator('.chat-form textarea').fill('Which code does the Orion emergency protocol require?')
    await page.getByRole('button', { name: 'Send' }).click()

    await expect(page.getByText(/Resposta simulada/)).toBeVisible()
    await expect(page.getByText('Retrieved sources')).toBeVisible()
    await page.locator('details.sources-block > summary').click()
    await expect(page.getByText(new RegExp(`${title} · chunk 0`))).toBeVisible()
    await page.locator('details.source-detail > summary').click()
    await expect(page.getByText(evidence)).toBeVisible()
  })
})
