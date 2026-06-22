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

const sampleDocument = `SoberanIA Labs Local RAG é uma aplicação local-first para conversar com documentos privados.
O projeto demonstra React, TypeScript, FastAPI, SQLite, Docker, CI e integração opcional com Ollama.
O modo mock/hash permite validar o fluxo em ambientes sem GPU ou modelo local.`

function App() {
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [title, setTitle] = useState('Documento de demonstração')
  const [content, setContent] = useState(sampleDocument)
  const [question, setQuestion] = useState(
    'Como este projeto permite conversar com documentos privados localmente?',
  )
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasDocuments = documents.length > 0

  const totalChunks = useMemo(
    () => documents.reduce((sum, document) => sum + document.total_chunks, 0),
    [documents],
  )

  const totalCharacters = useMemo(
    () => documents.reduce((sum, document) => sum + document.total_chars, 0),
    [documents],
  )

  const statusLabel = useMemo(() => {
    if (!config) return 'conectando'
    return `${config.llm_provider}/${config.embedding_provider}`
  }, [config])

  const modeDescription = useMemo(() => {
    if (!config) return 'Aguardando configuração pública da API.'
    if (config.llm_provider === 'mock' || config.embedding_provider === 'hash') {
      return 'Modo determinístico para validação sem modelos locais.'
    }
    return `Usando ${config.llm_model} com embeddings ${config.embedding_model}.`
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
      setError(caught instanceof Error ? caught.message : 'Falha ao adicionar texto à base.')
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
      setError(caught instanceof Error ? caught.message : 'Falha ao adicionar arquivo à base.')
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
      setError(caught instanceof Error ? caught.message : 'Falha ao conversar com a base local.')
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
      setError(caught instanceof Error ? caught.message : 'Falha ao remover documento da base.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="hero card">
        <div>
          <p className="eyebrow">SoberanIA Labs</p>
          <h1>Converse com documentos locais</h1>
          <p className="hero-copy">
            Adicione textos ou arquivos, indexe tudo em SQLite e pergunte à base usando RAG
            local-first com IA local opcional via Ollama/Gemma.
          </p>
        </div>
        <div className="status-cluster" aria-label="Status da aplicação">
          <div className="status-pill">
            <span className="status-dot" />
            {statusLabel}
          </div>
          <p>{modeDescription}</p>
        </div>
      </section>

      <section className="workflow-strip card" aria-label="Fluxo local RAG">
        <div>
          <span>1</span>
          <strong>Adicione documentos</strong>
          <p>Texto, Markdown, TXT ou PDF com texto selecionável.</p>
        </div>
        <div>
          <span>2</span>
          <strong>Confira a base local</strong>
          <p>{hasDocuments ? `${documents.length} documentos · ${totalChunks} chunks` : 'Nenhum documento ainda.'}</p>
        </div>
        <div>
          <span>3</span>
          <strong>Converse com a base</strong>
          <p>As respostas mostram fontes, score, modelo e latência.</p>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="grid two-columns ingest-grid">
        <form className="card stack" onSubmit={handleCreateDocument}>
          <div>
            <p className="eyebrow">Entrada rápida</p>
            <h2>Adicionar texto</h2>
            <p className="muted">Cole um trecho e transforme em fonte consultável.</p>
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
              rows={9}
            />
          </label>
          <button disabled={isLoading || title.trim().length === 0 || content.trim().length < 10}>
            Adicionar à base
          </button>
        </form>

        <form className="card stack" onSubmit={handleUploadDocument}>
          <div>
            <p className="eyebrow">Upload local</p>
            <h2>Adicionar arquivo</h2>
            <p className="muted">Use TXT, Markdown ou PDF com texto selecionável.</p>
          </div>
          <label className="upload-dropzone">
            <span>{selectedFile ? selectedFile.name : 'Escolher arquivo local'}</span>
            <small>
              {selectedFile
                ? `${Math.ceil(selectedFile.size / 1024)} KB prontos para indexar`
                : 'Arraste pela interface do sistema ou selecione um arquivo.'}
            </small>
            <input
              type="file"
              accept=".txt,.md,.markdown,.pdf"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <p className="muted">
            PDFs escaneados/OCR ficam fora do escopo. O conteúdo permanece na base local.
          </p>
          <button disabled={isLoading || !selectedFile}>Adicionar arquivo à base</button>
        </form>
      </section>

      <section className="grid two-columns workspace-grid">
        <section className="card stack base-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Base local</p>
              <h2>Documentos indexados</h2>
            </div>
            <strong>{documents.length}</strong>
          </div>

          <div className="metric-grid">
            <div>
              <span>Documentos</span>
              <strong>{documents.length}</strong>
            </div>
            <div>
              <span>Chunks</span>
              <strong>{totalChunks}</strong>
            </div>
            <div>
              <span>Caracteres</span>
              <strong>{totalCharacters.toLocaleString('pt-BR')}</strong>
            </div>
          </div>

          {!hasDocuments && (
            <div className="empty-state">
              <strong>A base ainda está vazia.</strong>
              <p>Adicione um texto ou arquivo para liberar perguntas com fontes recuperadas.</p>
            </div>
          )}

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
                  Remover da base
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="card stack chat-card">
          <div>
            <p className="eyebrow">Chat RAG</p>
            <h2>Converse com a base</h2>
            <p className="muted">
              {hasDocuments
                ? 'Pergunte sobre os documentos indexados e confira as fontes usadas.'
                : 'Adicione documentos antes de conversar com a base.'}
            </p>
          </div>
          <form className="chat-form" onSubmit={handleAskQuestion}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
            />
            <button disabled={isLoading || !hasDocuments || question.trim().length < 3}>
              Conversar com a base
            </button>
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
        <p className="eyebrow">Status técnico local</p>
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
