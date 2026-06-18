import { FormEvent, useEffect, useMemo, useState } from 'react'

import {
  askQuestion,
  createDocument,
  deleteDocument,
  getConfig,
  listDocuments,
  uploadDocument,
} from './api'
import type { ChatResponse, DocumentRecord, PublicConfig } from './types'

const sampleDocument = `SIALabs Local RAG é uma aplicação local-first para consultar documentos com RAG.
O projeto demonstra React, TypeScript, FastAPI, SQLite, Docker, CI e integração opcional com Ollama.
O modo mock/hash permite validar o fluxo em ambientes sem GPU ou modelo local.`

function App() {
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [title, setTitle] = useState('Documento de demonstração')
  const [content, setContent] = useState(sampleDocument)
  const [question, setQuestion] = useState('Quais competências técnicas este projeto demonstra?')
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasDocuments = documents.length > 0

  const statusLabel = useMemo(() => {
    if (!config) return 'conectando'
    return `${config.llm_provider}/${config.embedding_provider}`
  }, [config])

  async function refreshDocuments() {
    const records = await listDocuments()
    setDocuments(records)
  }

  useEffect(() => {
    async function boot() {
      try {
        const [publicConfig] = await Promise.all([getConfig()])
        setConfig(publicConfig)
        await refreshDocuments()
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'Falha ao conectar na API.')
      }
    }

    void boot()
  }, [])

  async function handleCreateDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      await createDocument({ title, content })
      setContent('')
      await refreshDocuments()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Falha ao criar documento.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleUploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedFile) return
    setIsLoading(true)
    setError(null)
    try {
      await uploadDocument(selectedFile)
      setSelectedFile(null)
      await refreshDocuments()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Falha ao enviar arquivo.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleAskQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      const response = await askQuestion(question)
      setChatResponse(response)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Falha ao consultar documentos.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleDeleteDocument(documentId: string) {
    setIsLoading(true)
    setError(null)
    try {
      await deleteDocument(documentId)
      await refreshDocuments()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Falha ao remover documento.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="hero card">
        <div>
          <p className="eyebrow">SoberanIA Labs</p>
          <h1>Local RAG Assistant</h1>
          <p className="hero-copy">
            Consulte documentos com RAG local-first, SQLite e IA local opcional via Ollama/Gemma.
          </p>
        </div>
        <div className="status-pill" aria-label="Status da API">
          <span className="status-dot" />
          {statusLabel}
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="grid two-columns">
        <form className="card stack" onSubmit={handleCreateDocument}>
          <div>
            <p className="eyebrow">Ingestão manual</p>
            <h2>Novo documento</h2>
          </div>
          <label>
            Título
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            Conteúdo
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              rows={10}
            />
          </label>
          <button disabled={isLoading || title.trim().length === 0 || content.trim().length < 10}>
            Indexar texto
          </button>
        </form>

        <form className="card stack" onSubmit={handleUploadDocument}>
          <div>
            <p className="eyebrow">Upload UTF-8</p>
            <h2>Arquivo .txt, .md ou .pdf</h2>
          </div>
          <input
            type="file"
            accept=".txt,.md,.markdown,.pdf"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
          <p className="muted">
            O MVP aceita TXT, Markdown e PDFs com texto selecionavel. PDFs escaneados/OCR
            ficam fora do escopo por enquanto.
          </p>
          <button disabled={isLoading || !selectedFile}>Enviar arquivo</button>
        </form>
      </section>

      <section className="grid two-columns">
        <section className="card stack">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Base local</p>
              <h2>Documentos indexados</h2>
            </div>
            <strong>{documents.length}</strong>
          </div>

          {!hasDocuments && <p className="muted">Nenhum documento indexado ainda.</p>}

          <div className="document-list">
            {documents.map((document) => (
              <article className="document-item" key={document.id}>
                <div>
                  <h3>{document.title}</h3>
                  <p>
                    {document.total_chunks} chunks · {document.total_chars} caracteres ·{' '}
                    {document.source_type}
                  </p>
                </div>
                <button
                  className="secondary"
                  onClick={() => void handleDeleteDocument(document.id)}
                  type="button"
                >
                  Remover
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="card stack">
          <div>
            <p className="eyebrow">Chat RAG</p>
            <h2>Pergunte à base</h2>
          </div>
          <form className="chat-form" onSubmit={handleAskQuestion}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
            />
            <button disabled={isLoading || question.trim().length < 3}>Perguntar</button>
          </form>

          {chatResponse && (
            <article className="answer-box">
              <div className="answer-meta">
                <span>{chatResponse.provider}</span>
                <span>{chatResponse.model}</span>
                <span>{chatResponse.latency_ms} ms</span>
              </div>
              <p>{chatResponse.answer}</p>
              <h3>Fontes recuperadas</h3>
              <div className="sources">
                {chatResponse.sources.map((source) => (
                  <details key={source.chunk_id}>
                    <summary>
                      {source.document_title} · chunk {source.chunk_index} · score {source.score}
                    </summary>
                    <p>{source.content}</p>
                  </details>
                ))}
              </div>
            </article>
          )}
        </section>
      </section>

      <section className="card config-card">
        <p className="eyebrow">Configuração pública</p>
        {config ? (
          <dl>
            <div>
              <dt>LLM</dt>
              <dd>
                {config.llm_provider} · {config.llm_model}
              </dd>
            </div>
            <div>
              <dt>Embeddings</dt>
              <dd>
                {config.embedding_provider} · {config.embedding_model}
              </dd>
            </div>
            <div>
              <dt>Retrieval</dt>
              <dd>top {config.retrieval_top_k}</dd>
            </div>
            <div>
              <dt>Chunking</dt>
              <dd>
                {config.chunk_size} chars · overlap {config.chunk_overlap}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="muted">Aguardando API.</p>
        )}
      </section>
    </main>
  )
}

export default App
