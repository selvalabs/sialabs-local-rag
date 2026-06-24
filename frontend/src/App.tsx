import { useEffect, useMemo, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'

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
type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  response?: ChatResponse
}

const CHAT_HISTORY_STORAGE_KEY = 'sialabs-local-rag-chat-history-v1'

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
    addText: 'Paste text document',
    addTextHelp: 'Paste a full document into the local base.',
    pasteDocument: 'Paste document',
    pasteModalTitle: 'Paste your document content',
    title: 'Title',
    content: 'Paste your document content',
    contentPlaceholder: 'Paste your document content here...',
    addToBase: 'Add to base',
    cancel: 'Cancel',
    uploadLocal: 'Local upload',
    addFile: 'Add file',
    addFileHelp: 'Choose a file or drag one anywhere into the app window.',
    chooseLocalFile: 'Choose file',
    fileReady: (kb: number) => `${kb} KB ready to add`,
    fileHint: 'TXT, Markdown or selectable-text PDF.',
    dropFile: 'Drop file to add it',
    pdfBoundary: 'Scanned PDFs/OCR are out of scope. Content stays in the local base.',
    addFileToBase: 'Add file',
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
    chatReady: 'Ask follow-up questions and inspect the sources used in each answer.',
    chatBlocked: 'Add documents before chatting with the base.',
    askBase: 'Send',
    clearChat: 'Clear chat',
    emptyChatTitle: 'No messages yet.',
    emptyChatText: 'Ask a question to start a local conversation with your documents.',
    userLabel: 'You',
    assistantLabel: 'Local assistant',
    thinking: 'Searching the local base and generating an answer…',
    sources: 'Retrieved sources',
    sourceSingular: 'source',
    sourcePlural: 'sources',
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
    heroTitle: 'Converse com documentos',
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
    addText: 'Colar documento em texto',
    addTextHelp: 'Cole um documento completo na base local.',
    pasteDocument: 'Colar documento',
    pasteModalTitle: 'Cole o conteúdo do documento',
    title: 'Título',
    content: 'Cole o conteúdo do documento',
    contentPlaceholder: 'Cole aqui o conteúdo do documento...',
    addToBase: 'Adicionar à base',
    cancel: 'Cancelar',
    uploadLocal: 'Upload local',
    addFile: 'Adicionar arquivo',
    addFileHelp: 'Escolha um arquivo ou arraste para qualquer lugar da janela.',
    chooseLocalFile: 'Escolher arquivo',
    fileReady: (kb: number) => `${kb} KB prontos para adicionar`,
    fileHint: 'TXT, Markdown ou PDF com texto selecionável.',
    dropFile: 'Solte o arquivo para adicionar',
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
    chatReady: 'Faça perguntas de continuidade e confira as fontes usadas em cada resposta.',
    chatBlocked: 'Adicione documentos antes de conversar com a base.',
    askBase: 'Enviar',
    clearChat: 'Limpar chat',
    emptyChatTitle: 'Nenhuma mensagem ainda.',
    emptyChatText: 'Faça uma pergunta para iniciar uma conversa local com seus documentos.',
    userLabel: 'Você',
    assistantLabel: 'Assistente local',
    thinking: 'Buscando na base local e gerando resposta…',
    sources: 'Fontes recuperadas',
    sourceSingular: 'fonte',
    sourcePlural: 'fontes',
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

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function isChatMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Partial<ChatMessage>
  return (
    typeof candidate.id === 'string' &&
    typeof candidate.content === 'string' &&
    (candidate.role === 'user' || candidate.role === 'assistant')
  )
}

function readPersistedChatMessages(): ChatMessage[] {
  if (typeof window === 'undefined') return []

  try {
    const storedMessages = window.localStorage.getItem(CHAT_HISTORY_STORAGE_KEY)
    if (!storedMessages) return []

    const parsed = JSON.parse(storedMessages) as unknown
    if (!Array.isArray(parsed)) return []

    return parsed.filter(isChatMessage)
  } catch {
    return []
  }
}

function buildContextualQuestion(messages: ChatMessage[], currentQuestion: string, language: Language) {
  const recentMessages = messages.slice(-6)
  if (recentMessages.length === 0) return currentQuestion

  const recentContext = recentMessages
    .map((message) => {
      const label =
        message.role === 'user'
          ? language === 'pt'
            ? 'Usuário'
            : 'User'
          : language === 'pt'
            ? 'Assistente'
            : 'Assistant'
      return `${label}: ${message.content}`
    })
    .join('\n\n')

  const contextualQuestion =
    language === 'pt'
      ? [
          'Contexto recente da conversa:',
          recentContext,
          '',
          'Pergunta atual do usuário:',
          currentQuestion,
        ].join('\n')
      : [
          'Recent conversation context:',
          recentContext,
          '',
          'Current user question:',
          currentQuestion,
        ].join('\n')

  if (contextualQuestion.length <= 3800) return contextualQuestion
  return contextualQuestion.slice(contextualQuestion.length - 3800)
}

function isFileDrag(event: DragEvent) {
  return Array.from(event.dataTransfer?.types ?? []).includes('Files')
}

function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [theme, setTheme] = useState<Theme>('light')
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [title, setTitle] = useState(copy.en.defaultTitle as string)
  const [content, setContent] = useState(sampleDocuments.en)
  const [question, setQuestion] = useState(copy.en.defaultQuestion as string)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(readPersistedChatMessages)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isPasteModalOpen, setIsPasteModalOpen] = useState(false)
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const t = copy[language]
  const hasDocuments = documents.length > 0
  const hasChatMessages = chatMessages.length > 0

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

  useEffect(() => {
    let dragDepth = 0

    function handleDragEnter(event: DragEvent) {
      if (!isFileDrag(event)) return
      event.preventDefault()
      dragDepth += 1
      setIsDraggingFile(true)
    }

    function handleDragOver(event: DragEvent) {
      if (!isFileDrag(event)) return
      event.preventDefault()
      if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
    }

    function handleDragLeave(event: DragEvent) {
      if (!isFileDrag(event)) return
      event.preventDefault()
      dragDepth = Math.max(0, dragDepth - 1)
      if (dragDepth === 0) setIsDraggingFile(false)
    }

    function handleDrop(event: DragEvent) {
      if (!isFileDrag(event)) return
      event.preventDefault()
      dragDepth = 0
      setIsDraggingFile(false)
      const droppedFile = event.dataTransfer?.files?.[0]
      if (droppedFile) setSelectedFile(droppedFile)
    }

    window.addEventListener('dragenter', handleDragEnter)
    window.addEventListener('dragover', handleDragOver)
    window.addEventListener('dragleave', handleDragLeave)
    window.addEventListener('drop', handleDrop)

    return () => {
      window.removeEventListener('dragenter', handleDragEnter)
      window.removeEventListener('dragover', handleDragOver)
      window.removeEventListener('dragleave', handleDragLeave)
      window.removeEventListener('drop', handleDrop)
    }
  }, [])

  useEffect(() => {
    try {
      if (chatMessages.length === 0) {
        window.localStorage.removeItem(CHAT_HISTORY_STORAGE_KEY)
        return
      }
      window.localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(chatMessages))
    } catch {
      // Local storage can be unavailable in restricted browser contexts.
    }
  }, [chatMessages])

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
      setIsPasteModalOpen(false)
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

  async function submitQuestion() {
    const submittedQuestion = question.trim()
    if (submittedQuestion.length < 3 || isLoading || !hasDocuments) return

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: 'user',
      content: submittedQuestion,
    }
    const priorMessages = chatMessages
    setChatMessages((currentMessages) => [...currentMessages, userMessage])
    setQuestion('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await askQuestion(
        buildContextualQuestion(priorMessages, submittedQuestion, language),
      )
      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        role: 'assistant',
        content: response.answer,
        response,
      }
      setChatMessages((currentMessages) => [...currentMessages, assistantMessage])
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (t.chatError as string))
      setQuestion(submittedQuestion)
    } finally {
      setIsLoading(false)
    }
  }

  function handleAskQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submitQuestion()
  }

  function handleQuestionKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== 'Enter' || event.shiftKey) return
    event.preventDefault()
    void submitQuestion()
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
      {isDraggingFile && <div className="drop-overlay">{t.dropFile as string}</div>}

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
        <section className="card action-card">
          <div className="action-card-copy">
            <p className="eyebrow">{t.quickEntry as string}</p>
            <h2>{t.addText as string}</h2>
            <p className="muted">{t.addTextHelp as string}</p>
          </div>
          <button className="action-button" onClick={() => setIsPasteModalOpen(true)} type="button">
            {t.pasteDocument as string}
          </button>
        </section>

        <form className="card action-card upload-card" onSubmit={handleUploadDocument}>
          <div className="action-card-copy">
            <p className="eyebrow">{t.uploadLocal as string}</p>
            <h2>{t.addFile as string}</h2>
            <p className="muted">{t.addFileHelp as string}</p>
            {selectedFile && <p className="selected-file-meta">{selectedFile.name}</p>}
          </div>
          {selectedFile ? (
            <button className="action-button" disabled={isLoading} type="submit">
              {t.addFileToBase as string}
            </button>
          ) : (
            <label className="action-button file-action-button">
              {t.chooseLocalFile as string}
              <input
                type="file"
                accept=".txt,.md,.markdown,.pdf"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </label>
          )}
        </form>
      </section>

      <section className="grid workspace-grid">
        <details className="card stack base-card toggle-card">
          <summary className="toggle-summary">
            <span>
              <span className="eyebrow">{t.localBase as string}</span>
              <strong>{t.indexedDocs as string}</strong>
            </span>
            <span className="summary-pill">{documents.length}</span>
          </summary>

          <div className="stack toggle-content">
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

            <div className="document-list document-list-scroll">
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
          </div>
        </details>

        <section className="card stack chat-card primary-chat-card">
          <div className="chat-heading">
            <div>
              <p className="eyebrow">{t.chatRag as string}</p>
              <h2>{t.chatWithBase as string}</h2>
              <p className="muted">
                {hasDocuments ? (t.chatReady as string) : (t.chatBlocked as string)}
              </p>
            </div>
            {hasChatMessages && (
              <button className="ghost" onClick={() => setChatMessages([])} type="button">
                {t.clearChat as string}
              </button>
            )}
          </div>

          <div className="conversation-log" aria-live="polite">
            {!hasChatMessages && !isLoading && (
              <div className="conversation-empty">
                <strong>{t.emptyChatTitle as string}</strong>
                <p>{t.emptyChatText as string}</p>
              </div>
            )}

            {chatMessages.map((message) => (
              <article className={`chat-message ${message.role}`} key={message.id}>
                <span className="message-label">
                  {message.role === 'user' ? (t.userLabel as string) : (t.assistantLabel as string)}
                </span>
                {message.response && (
                  <div className="answer-meta">
                    <span>{message.response.provider}</span>
                    <span>{message.response.model}</span>
                    <span>{message.response.latency_ms} ms</span>
                  </div>
                )}
                <p>{message.content}</p>
                {message.response && (
                  <details className="sources-block">
                    <summary>
                      <span>{t.sources as string}</span>
                      <span className="sources-count">
                        {message.response.sources.length}{' '}
                        {message.response.sources.length === 1
                          ? (t.sourceSingular as string)
                          : (t.sourcePlural as string)}
                      </span>
                    </summary>
                    <div className="sources">
                      {message.response.sources.map((source) => (
                        <details className="source-detail" key={`${message.id}-${source.chunk_id}`}>
                          <summary>
                            {source.document_title} · chunk {source.chunk_index} · score {source.score}
                          </summary>
                          <p>{source.content}</p>
                        </details>
                      ))}
                    </div>
                  </details>
                )}
              </article>
            ))}

            {isLoading && (
              <article className="chat-message assistant pending">
                <span className="message-label">{t.assistantLabel as string}</span>
                <p>{t.thinking as string}</p>
              </article>
            )}
          </div>

          <form className="chat-form" onSubmit={handleAskQuestion}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleQuestionKeyDown}
              rows={4}
            />
            <button disabled={isLoading || !hasDocuments || question.trim().length < 3}>
              {t.askBase as string}
            </button>
          </form>
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

      {isPasteModalOpen && (
        <div className="modal-backdrop" role="presentation">
          <section className="card stack modal-card" role="dialog" aria-modal="true">
            <div className="chat-heading">
              <div>
                <p className="eyebrow">{t.quickEntry as string}</p>
                <h2>{t.pasteModalTitle as string}</h2>
              </div>
              <button className="ghost" onClick={() => setIsPasteModalOpen(false)} type="button">
                {t.cancel as string}
              </button>
            </div>
            <form className="stack" onSubmit={handleCreateDocument}>
              <label>
                {t.title as string}
                <input value={title} onChange={(event) => setTitle(event.target.value)} />
              </label>
              <label>
                {t.content as string}
                <textarea
                  autoFocus
                  placeholder={t.contentPlaceholder as string}
                  value={content}
                  onChange={(event) => setContent(event.target.value)}
                  rows={14}
                />
              </label>
              <div className="modal-actions">
                <button className="secondary" onClick={() => setIsPasteModalOpen(false)} type="button">
                  {t.cancel as string}
                </button>
                <button disabled={isLoading || title.trim().length === 0 || content.trim().length < 10}>
                  {t.addToBase as string}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </main>
  )
}

export default App
