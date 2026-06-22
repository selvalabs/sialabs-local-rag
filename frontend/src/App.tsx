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

type Language = 'en' | 'pt'
type Theme = 'light' | 'dark'

const sampleDocuments: Record<Language, string> = {
  en: `SoberanIA Labs Local RAG is a local-first application for chatting with private documents.
The project demonstrates React, TypeScript, FastAPI, SQLite, Docker, CI and optional Ollama integration.
The mock/hash mode validates the full flow on machines without a GPU or local model.`,
  pt: `SoberanIA Labs Local RAG é uma aplicação local-first para conversar com documentos privados.
O projeto demonstra React, TypeScript, FastAPI, SQLite, Docker, CI e integração opcional com Ollama.
O modo mock/hash permite validar o fluxo em ambientes sem GPU ou modelo local.`,
}

const copy = {
  en: {
    connecting: 'connecting',
    waitingApi: 'Waiting for public API configuration.',
    mockMode: 'Deterministic validation mode without local models.',
    usingModel: (model: string, embedding: string) => `Using ${model} with ${embedding} embeddings.`,
    heroTitle: 'Chat with local documents',
    heroCopy:
      'Add text or files, index everything in SQLite, and ask your local base using local-first RAG with optional Ollama/Gemma AI.',
    stepOneTitle: 'Add documents',
    stepOneText: 'Text, Markdown, TXT or selectable-text PDF.',
    stepTwoTitle: 'Check the local base',
    stepTwoEmpty: 'No documents yet.',
    stepTwoFilled: (docs: number, chunks: number) => `${docs} documents · ${chunks} chunks`,
    stepThreeTitle: 'Chat with the base',
    stepThreeText: 'Answers show sources, score, model and latency.',
    quickEntry: 'Quick entry',
    addText: 'Add text',
    addTextHelp: 'Paste a passage and turn it into a searchable source.',
    title: 'Title',
    content: 'Content',
    addToBase: 'Add to base',
    uploadLocal: 'Local upload',
    addFile: 'Add file',
    addFileHelp: 'Use TXT, Markdown or selectable-text PDF.',
    chooseLocalFile: 'Choose local file',
    fileReady: (kb: number) => `${kb} KB ready to index`,
    fileHint: 'Select a file from your system.',
    pdfBoundary: 'Scanned PDFs/OCR are out of scope. Content stays in the local base.',
    addFileToBase: 'Add file to base',
    localBase: 'Local base',
    indexedDocs: 'Indexed documents',
    documents: 'Documents',
    chunks: 'Chunks',
    characters: 'Characters',
    emptyTitle: 'The base is still empty.',
    emptyText: 'Add text or a file to unlock questions with retrieved sources.',
    removeFromBase: 'Remove from base',
    chatRag: 'RAG chat',
    chatWithBase: 'Chat with the base',
    chatReady: 'Ask about indexed documents and inspect the retrieved sources.',
    chatBlocked: 'Add documents before chatting with the base.',
    askBase: 'Chat with the base',
    sources: 'Retrieved sources',
    techStatus: 'Local technical status',
    llm: 'LLM',
    embeddings: 'Embeddings',
    retrieval: 'Retrieval',
    chunking: 'Chunking',
    apiWaiting: 'Waiting for API.',
    defaultTitle: 'Demo document',
    defaultQuestion: 'How does this project let you chat with private documents locally?',
    createError: 'Failed to add text to the base.',
    uploadError: 'Failed to add file to the base.',
    chatError: 'Failed to chat with the local base.',
    deleteError: 'Failed to remove document from the base.',
    apiError: 'Failed to connect to the API.',
  },
  pt: {
    connecting: 'conectando',
    waitingApi: 'Aguardando configuração pública da API.',
    mockMode: 'Modo determinístico para validação sem modelos locais.',
    usingModel: (model: string, embedding: string) => `Usando ${model} com embeddings ${embedding}.`,
    heroTitle: 'Converse com documentos locais',
    heroCopy:
      'Adicione textos ou arquivos, indexe tudo em SQLite e pergunte à base usando RAG local-first com IA local opcional via Ollama/Gemma.',
    stepOneTitle: 'Adicione documentos',
    stepOneText: 'Texto, Markdown, TXT ou PDF com texto selecionável.',
    stepTwoTitle: 'Confira a base local',
    stepTwoEmpty: 'Nenhum documento ainda.',
    stepTwoFilled: (docs: number, chunks: number) => `${docs} documentos · ${chunks} chunks`,
    stepThreeTitle: 'Converse com a base',
    stepThreeText: 'As respostas mostram fontes, score, modelo e latência.',
    quickEntry: 'Entrada rápida',
    addText: 'Adicionar texto',
    addTextHelp: 'Cole um trecho e transforme em fonte consultável.',
    title: 'Título',
    content: 'Conteúdo',
    addToBase: 'Adicionar à base',
    uploadLocal: 'Upload local',
    addFile: 'Adicionar arquivo',
    addFileHelp: 'Use TXT, Markdown ou PDF com texto selecionável.',
    chooseLocalFile: 'Escolher arquivo local',
    fileReady: (kb: number) => `${kb} KB prontos para indexar`,
    fileHint: 'Selecione um arquivo do seu sistema.',
    pdfBoundary: 'PDFs escaneados/OCR ficam fora do escopo. O conteúdo permanece na base local.',
    addFileToBase: 'Adicionar arquivo',
    localBase: 'Base local',
    indexedDocs: 'Documentos indexados',
    documents: 'Documentos',
    chunks: 'Chunks',
    characters: 'Caracteres',
    emptyTitle: 'A base ainda está vazia.',
    emptyText: 'Adicione um texto ou arquivo para liberar perguntas com fontes recuperadas.',
    removeFromBase: 'Remover da base',
    chatRag: 'Chat RAG',
    chatWithBase: 'Converse com a base',
    chatReady: 'Pergunte sobre os documentos indexados e confira as fontes usadas.',
    chatBlocked: 'Adicione documentos antes de conversar com a base.',
    askBase: 'Conversar com a base',
    sources: 'Fontes recuperadas',
    techStatus: 'Status técnico local',
    llm: 'LLM',
    embeddings: 'Embeddings',
    retrieval: 'Retrieval',
    chunking: 'Chunking',
    apiWaiting: 'Aguardando API.',
    defaultTitle: 'Documento de demonstração',
    defaultQuestion: 'Como este projeto permite conversar com documentos privados localmente?',
    createError: 'Falha ao adicionar texto à base.',
    uploadError: 'Falha ao adicionar arquivo à base.',
    chatError: 'Falha ao conversar com a base local.',
    deleteError: 'Falha ao remover documento da base.',
    apiError: 'Falha ao conectar na API.',
  },
} satisfies Record<Language, Record<string, unknown>>

function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [theme, setTheme] = useState<Theme>('light')
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [title, setTitle] = useState(copy.en.defaultTitle as string)
  const [content, setContent] = useState(sampleDocuments.en)
  const [question, setQuestion] = useState(copy.en.defaultQuestion as string)
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const t = copy[language]
  const hasDocuments = documents.length > 0

  const totalChunks = useMemo(
    () => documents.reduce((sum, document) => sum + document.total_chunks, 0),
    [documents],
  )

  const totalCharacters = useMemo(
    () => documents.reduce((sum, document) => sum + document.total_chars, 0),
    [documents],
  )

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.lang = language
  }, [language, theme])

  const statusLabel = useMemo(() => {
    if (!config) return t.connecting as string
    return `${config.llm_provider}/${config.embedding_provider}`
  }, [config, t])

  const modeDescription = useMemo(() => {
    if (!config) return t.waitingApi as string
    if (config.llm_provider === 'mock' || config.embedding_provider === 'hash') {
      return t.mockMode as string
    }
    return (t.usingModel as (model: string, embedding: string) => string)(
      config.llm_model,
      config.embedding_model,
    )
  }, [config, t])

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
        setError(caught instanceof Error ? caught.message : (t.apiError as string))
      }
    }

    void boot()
  }, [t])

  function handleLanguageChange(nextLanguage: Language) {
    setLanguage(nextLanguage)
    if (!title.trim() || title === copy.en.defaultTitle || title === copy.pt.defaultTitle) {
      setTitle(copy[nextLanguage].defaultTitle as string)
    }
    if (!content.trim() || content === sampleDocuments.en || content === sampleDocuments.pt) {
      setContent(sampleDocuments[nextLanguage])
    }
    if (
      !question.trim() ||
      question === copy.en.defaultQuestion ||
      question === copy.pt.defaultQuestion
    ) {
      setQuestion(copy[nextLanguage].defaultQuestion as string)
    }
  }

  async function handleCreateDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      await createDocument({ title, content })
      setContent('')
      await refreshDocuments()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (t.createError as string))
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
      setError(caught instanceof Error ? caught.message : (t.uploadError as string))
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
      setError(caught instanceof Error ? caught.message : (t.chatError as string))
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
      setError(caught instanceof Error ? caught.message : (t.deleteError as string))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app-shell" data-theme={theme}>
      <section className="hero card">
        <div>
          <p className="eyebrow">SoberanIA Labs</p>
          <h1>{t.heroTitle as string}</h1>
          <p className="hero-copy">{t.heroCopy as string}</p>
        </div>
        <div className="status-cluster" aria-label="Application status">
          <div className="toolbar" aria-label="Display controls">
            <button
              className="ghost"
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              type="button"
            >
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
            <button
              className="ghost"
              onClick={() => handleLanguageChange(language === 'en' ? 'pt' : 'en')}
              type="button"
            >
              {language === 'en' ? 'PT' : 'EN'}
            </button>
          </div>
          <div className="status-pill">
            <span className="status-dot" />
            {statusLabel}
          </div>
          <p>{modeDescription}</p>
        </div>
      </section>

      <section className="workflow-strip card" aria-label="Local RAG flow">
        <div>
          <span>1</span>
          <strong>{t.stepOneTitle as string}</strong>
          <p>{t.stepOneText as string}</p>
        </div>
        <div>
          <span>2</span>
          <strong>{t.stepTwoTitle as string}</strong>
          <p>
            {hasDocuments
              ? (t.stepTwoFilled as (docs: number, chunks: number) => string)(
                  documents.length,
                  totalChunks,
                )
              : (t.stepTwoEmpty as string)}
          </p>
        </div>
        <div>
          <span>3</span>
          <strong>{t.stepThreeTitle as string}</strong>
          <p>{t.stepThreeText as string}</p>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="grid two-columns ingest-grid">
        <form className="card stack" onSubmit={handleCreateDocument}>
          <div>
            <p className="eyebrow">{t.quickEntry as string}</p>
            <h2>{t.addText as string}</h2>
            <p className="muted">{t.addTextHelp as string}</p>
          </div>
          <label>
            {t.title as string}
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            {t.content as string}
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              rows={9}
            />
          </label>
          <button disabled={isLoading || title.trim().length === 0 || content.trim().length < 10}>
            {t.addToBase as string}
          </button>
        </form>

        <form className="card stack upload-card" onSubmit={handleUploadDocument}>
          <div>
            <p className="eyebrow">{t.uploadLocal as string}</p>
            <h2>{t.addFile as string}</h2>
            <p className="muted">{t.addFileHelp as string}</p>
          </div>
          <label className="upload-dropzone">
            <span>{selectedFile ? selectedFile.name : (t.chooseLocalFile as string)}</span>
            <small>
              {selectedFile
                ? (t.fileReady as (kb: number) => string)(Math.ceil(selectedFile.size / 1024))
                : (t.fileHint as string)}
            </small>
            <input
              type="file"
              accept=".txt,.md,.markdown,.pdf"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <p className="muted">{t.pdfBoundary as string}</p>
          <button disabled={isLoading || !selectedFile}>{t.addFileToBase as string}</button>
        </form>
      </section>

      <section className="grid two-columns workspace-grid">
        <section className="card stack base-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{t.localBase as string}</p>
              <h2>{t.indexedDocs as string}</h2>
            </div>
            <strong>{documents.length}</strong>
          </div>

          <div className="metric-grid">
            <div>
              <span>{t.documents as string}</span>
              <strong>{documents.length}</strong>
            </div>
            <div>
              <span>{t.chunks as string}</span>
              <strong>{totalChunks}</strong>
            </div>
            <div>
              <span>{t.characters as string}</span>
              <strong>{totalCharacters.toLocaleString(language === 'pt' ? 'pt-BR' : 'en-US')}</strong>
            </div>
          </div>

          {!hasDocuments && (
            <div className="empty-state">
              <strong>{t.emptyTitle as string}</strong>
              <p>{t.emptyText as string}</p>
            </div>
          )}

          <div className="document-list">
            {documents.map((document) => (
              <article className="document-item" key={document.id}>
                <div>
                  <h3>{document.title}</h3>
                  <p>
                    {document.total_chunks} chunks · {document.total_chars} chars ·{' '}
                    {document.source_type}
                  </p>
                </div>
                <button
                  className="secondary"
                  onClick={() => void handleDeleteDocument(document.id)}
                  type="button"
                >
                  {t.removeFromBase as string}
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="card stack chat-card">
          <div>
            <p className="eyebrow">{t.chatRag as string}</p>
            <h2>{t.chatWithBase as string}</h2>
            <p className="muted">{hasDocuments ? (t.chatReady as string) : (t.chatBlocked as string)}</p>
          </div>
          <form className="chat-form" onSubmit={handleAskQuestion}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
            />
            <button disabled={isLoading || !hasDocuments || question.trim().length < 3}>
              {t.askBase as string}
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
              <h3>{t.sources as string}</h3>
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
        <p className="eyebrow">{t.techStatus as string}</p>
        {config ? (
          <dl>
            <div>
              <dt>{t.llm as string}</dt>
              <dd>
                {config.llm_provider} · {config.llm_model}
              </dd>
            </div>
            <div>
              <dt>{t.embeddings as string}</dt>
              <dd>
                {config.embedding_provider} · {config.embedding_model}
              </dd>
            </div>
            <div>
              <dt>{t.retrieval as string}</dt>
              <dd>top {config.retrieval_top_k}</dd>
            </div>
            <div>
              <dt>{t.chunking as string}</dt>
              <dd>
                {config.chunk_size} chars · overlap {config.chunk_overlap}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="muted">{t.apiWaiting as string}</p>
        )}
      </section>
    </main>
  )
}

export default App
