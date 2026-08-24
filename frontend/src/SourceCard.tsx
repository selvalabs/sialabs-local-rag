import type { SourceChunk } from './types'

type SourceCardLanguage = 'en' | 'pt'

function formatSourceLocator(source: SourceChunk, language: SourceCardLanguage): string | null {
  if (source.source_locator) return source.source_locator

  const labels: string[] = []
  if (source.section_title) labels.push(`${language === 'pt' ? 'Seção' : 'Section'}: ${source.section_title}`)
  if (source.page_number !== null && source.page_number !== undefined) {
    labels.push(`${language === 'pt' ? 'Página' : 'Page'} ${source.page_number}`)
  }
  if (source.slide_number !== null && source.slide_number !== undefined) {
    labels.push(`Slide ${source.slide_number}`)
  }
  if (source.sheet_name) labels.push(`${language === 'pt' ? 'Planilha' : 'Sheet'}: ${source.sheet_name}`)
  if (source.cell_range) labels.push(`${language === 'pt' ? 'Intervalo' : 'Range'} ${source.cell_range}`)
  return labels.length > 0 ? labels.join(' · ') : null
}

type SourceCardProps = {
  source: SourceChunk
  sourceIndex: number
  language: SourceCardLanguage
}

export function SourceCard({ source, sourceIndex, language }: SourceCardProps) {
  const locator = formatSourceLocator(source, language)
  const score = source.fusion_score ?? source.score

  return (
    <details className="source-detail">
      <summary>
        <span className="source-id">{`S${sourceIndex + 1}`}</span>{' '}
        {source.document_title} · chunk {source.chunk_index} · {source.retrieval_channels?.join('+') || 'retrieval'} · score {score}
      </summary>
      {locator && <p className="source-locator">{locator}</p>}
      <p>{source.content}</p>
    </details>
  )
}
