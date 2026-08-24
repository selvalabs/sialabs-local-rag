import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { SourceCard } from './SourceCard'
import type { SourceChunk } from './types'

describe('SourceCard', () => {
  it('renders one compact summary for each source', () => {
    const source: SourceChunk = {
      chunk_id: 'chunk-1',
      document_id: 'document-1',
      document_title: 'Demo document',
      chunk_index: 2,
      score: 0.42,
      content: 'Evidence content',
      source_locator: 'page:3',
      retrieval_channels: ['dense', 'lexical'],
      fusion_score: 0.84,
    }

    const markup = renderToStaticMarkup(<SourceCard source={source} sourceIndex={0} language="en" />)

    expect(markup.match(/S1/g) ?? []).toHaveLength(1)
    expect(markup.match(/Demo document/g) ?? []).toHaveLength(1)
    expect(markup).toContain('dense+lexical')
    expect(markup).toContain('page:3')
  })
})
