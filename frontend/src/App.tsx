import { useEffect, useMemo, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'

import {
  askQuestion,
  clearChatHistory,
  createDocument,
  getCollections,
  getConfig,
  getIndexStatus,
  getRuntimeConfig,
  resetIndex,
  testRuntime,
  uploadDocument,
} from './api'
import { SourceCard } from './SourceCard'
import type {
  ChatResponse,
  CollectionSummary,
  ConversationContextMessage,
  PublicConfig,
  RuntimeConfig,
  RuntimeOptions,
  RuntimeProfileName,
  RuntimeTestResponse,
  IndexStatusResponse,
} from './types'
import { useDocuments } from './hooks/useDocuments'

type Language = 'en' | 'pt'
type Theme = 'light' | 'dark'
type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  response?: ChatResponse
}
type UploadStatus = 'idle' | 'selected' | 'uploading' | 'ready' | 'error'

const CHAT_HISTORY_STORAGE_KEY = 'sialabs-local-rag-chat-history-v1'

const sampleDocuments: Record<Language, string> = {
  en: `SoberanIA Labs Local RAG is a local-first application for chatting with private documents.
The project demonstrates React, TypeScript, FastAPI, SQLite, Docker, CI and optional Ollama integration.
The mock/hash mode validates the full flow on machines without a GPU or local model.`,
  pt: `SoberanIA Labs Local RAG é uma aplicação local-first para conversar com documentos privados.
O projeto demonstra React, TypeScript, FastAPI, SQLite, Docker, CI e integração opcional com Ollama.
O modo mock/hash permite validar o fluxo em ambientes sem GPU ou modelo local.`,
}

const fallbackRuntimeProfiles: Record<RuntimeProfileName, RuntimeOptions> = {
  economy: {
    profile: 'economy',
    model: 'gemma4:e2b',
    num_ctx: 2048,
    num_gpu: 0,
    keep_alive: '1m',
    temperature: 0.2,
    think: false,
  },
  balanced: {
    profile: 'balanced',
    model: 'gemma4:e2b',
    num_ctx: 1024,
    num_gpu: null,
    keep_alive: '5m',
    temperature: 0.2,
    think: false,
  },
  strong: {
    profile: 'strong',
    model: 'gemma4:e2b',
    num_ctx: 4096,
    num_gpu: null,
    keep_alive: '5m',
    temperature: 0.2,
    think: true,
  },
  custom: {
    profile: 'custom',
    model: 'gemma4:e2b',
    num_ctx: 1024,
    num_gpu: null,
    keep_alive: '5m',
    temperature: 0.2,
    think: false,
  },
}

const copy = {
  en: {
    connecting: 'connecting',
    waitingApi: 'Waiting for public API configuration.',
    mockMode: 'Deterministic validation mode without local models.',
    usingModel: (model: string, embedding: string) => `Using ${model} with ${embedding} embeddings.`,
    heroTitle: 'Chat with local documents',
    skipMain: 'Skip to main content',
    darkTheme: 'Dark',
    lightTheme: 'Light',
    heroCopy:
      'Add text or files, index everything in SQLite, and ask your local base using local-first RAG with optional Ollama/Gemma AI.',
    stepOneTitle: 'Add documents',
    stepOneText: 'Text, Markdown, TXT or selectable-text PDF.',
    stepTwoTitle: 'Check the local base',
    stepTwoEmpty: 'No documents yet.',
    stepTwoFilled: (docs: number, chunks: number) => `${docs} ${docs === 1 ? 'document' : 'documents'} · ${chunks} ${chunks === 1 ? 'chunk' : 'chunks'}`,
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
    fileHint: 'TXT, Markdown, PDF, Office documents or images with optional OCR.',
    dropFile: 'Drop file to add it',
    pdfBoundary: 'Scanned PDFs/OCR are out of scope. Content stays in the local base.',
    addFileToBase: 'Add file',
    uploadSelected: 'Selected — ready to add',
    uploadIndexing: 'Uploading and indexing…',
    uploadReady: 'File indexed and ready',
    uploadFailed: 'File could not be indexed',
    localBase: 'Local base',
    indexedDocs: 'Indexed documents',
    documents: 'Documents',
    chunks: 'Chunks',
    characters: 'Characters',
    activeSources: (count: number) => `${count} ${count === 1 ? 'active source' : 'active sources'}`,
    documentCount: (count: number) => `${count} ${count === 1 ? 'document' : 'documents'}`,
    chunkCount: (count: number) => `${count} ${count === 1 ? 'chunk' : 'chunks'}`,
    characterCount: (count: number) => `${count} ${count === 1 ? 'character' : 'characters'}`,
    overlap: 'overlap',
    emptyTitle: 'The base is still empty.',
    emptyText: 'Add text or a file to unlock questions with retrieved sources.',
    removeFromBase: 'Remove from base',
    chatRag: 'RAG chat',
    chatWithBase: 'Chat with the base',
    chatReady: 'Ask follow-up questions and inspect the sources used in each answer.',
    chatBlocked: 'Add documents before chatting with the base.',
    collections: 'Collection',
    allCollections: 'All collections',
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
    copyAnswer: 'Copy answer',
    copied: 'Copied',
    runtimeSettings: 'AI runtime settings',
    runtimeSettingsText: 'Choose how much local memory and GPU the Ollama model may use.',
    runtimeProfile: 'Runtime profile',
    economyProfile: 'Economy',
    balancedProfile: 'Balanced',
    strongProfile: 'Strong',
    customProfile: 'Custom',
    model: 'Model',
    contextWindow: 'Context tokens',
    gpuLayers: 'GPU layers',
    gpuAuto: 'auto',
    keepAlive: 'Keep alive',
    keepAliveAuto: 'keep_alive auto',
    temperature: 'Temperature',
    thinkingSetting: 'Thinking',
    thinkingOn: 'Thinking on',
    thinkingOff: 'Thinking off',
    testRuntime: 'Test local AI',
    testingRuntime: 'Testing…',
    runtimeSuccess: 'Runtime test passed',
    runtimeFailure: 'Runtime test failed',
    runtimeUnavailable: 'Runtime settings unavailable until the API is reachable.',
    techStatus: 'Local technical status',
    indexHealth: 'Index health',
    resetIndex: 'Reset index',
    resetIndexConfirm: 'Reset the local index and remove all indexed documents?',
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
    runtimeError: 'Failed to test the local AI runtime.',
  },
  pt: {
    connecting: 'conectando',
    waitingApi: 'Aguardando configuração pública da API.',
    mockMode: 'Modo determinístico para validação sem modelos locais.',
    usingModel: (model: string, embedding: string) => `Usando ${model} com embeddings ${embedding}.`,
    heroTitle: 'Converse com documentos',
    skipMain: 'Ir para o conteúdo principal',
    darkTheme: 'Escuro',
    lightTheme: 'Claro',
    heroCopy:
      'Adicione textos ou arquivos, indexe tudo em SQLite e pergunte à base usando RAG local-first com IA local opcional via Ollama/Gemma.',
    stepOneTitle: 'Adicione documentos',
    stepOneText: 'Texto, Markdown, TXT ou PDF com texto selecionável.',
    stepTwoTitle: 'Confira a base local',
    stepTwoEmpty: 'Nenhum documento ainda.',
    stepTwoFilled: (docs: number, chunks: number) => `${docs} documento${docs === 1 ? '' : 's'} · ${chunks} chunk${chunks === 1 ? '' : 's'}`,
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
    fileHint: 'TXT, Markdown, PDF, documentos Office ou imagens com OCR opcional.',
    dropFile: 'Solte o arquivo para adicionar',
    pdfBoundary: 'PDFs escaneados/OCR ficam fora do escopo. O conteúdo permanece na base local.',
    addFileToBase: 'Adicionar arquivo',
    uploadSelected: 'Selecionado — pronto para adicionar',
    uploadIndexing: 'Enviando e indexando…',
    uploadReady: 'Arquivo indexado e pronto',
    uploadFailed: 'Não foi possível indexar o arquivo',
    localBase: 'Base local',
    indexedDocs: 'Documentos indexados',
    documents: 'Documentos',
    chunks: 'Chunks',
    characters: 'Caracteres',
    activeSources: (count: number) => `${count} fonte${count === 1 ? '' : 's'} ativa${count === 1 ? '' : 's'}`,
    documentCount: (count: number) => `${count} documento${count === 1 ? '' : 's'}`,
    chunkCount: (count: number) => `${count} chunk${count === 1 ? '' : 's'}`,
    characterCount: (count: number) => `${count} caractere${count === 1 ? '' : 's'}`,
    overlap: 'sobreposição',
    emptyTitle: 'A base ainda está vazia.',
    emptyText: 'Adicione um texto ou arquivo para liberar perguntas com fontes recuperadas.',
    removeFromBase: 'Remover da base',
    chatRag: 'Chat RAG',
    chatWithBase: 'Converse com a base',
    chatReady: 'Faça perguntas de continuidade e confira as fontes usadas em cada resposta.',
    chatBlocked: 'Adicione documentos antes de conversar com a base.',
    collections: 'Coleção',
    allCollections: 'Todas as coleções',
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
    copyAnswer: 'Copiar resposta',
    copied: 'Copiado',
    runtimeSettings: 'Configuração da IA local',
    runtimeSettingsText: 'Escolha quanta memória local e GPU o modelo do Ollama pode usar.',
    runtimeProfile: 'Perfil de uso',
    economyProfile: 'Econômico',
    balancedProfile: 'Equilibrado',
    strongProfile: 'Forte',
    customProfile: 'Personalizado',
    model: 'Modelo',
    contextWindow: 'Tokens de contexto',
    gpuLayers: 'Camadas GPU',
    gpuAuto: 'auto',
    keepAlive: 'Manter carregado',
    keepAliveAuto: 'keep_alive automático',
    temperature: 'Temperatura',
    thinkingSetting: 'Raciocínio',
    thinkingOn: 'Raciocínio ativado',
    thinkingOff: 'Raciocínio desativado',
    testRuntime: 'Testar IA local',
    testingRuntime: 'Testando…',
    runtimeSuccess: 'Teste da IA aprovado',
    runtimeFailure: 'Teste da IA falhou',
    runtimeUnavailable: 'Configuração indisponível até a API responder.',
    techStatus: 'Status técnico local',
    indexHealth: 'Saúde do índice',
    resetIndex: 'Reindexar base',
    resetIndexConfirm: 'Recriar o índice local e remover todos os documentos indexados?',
    llm: 'LLM',
    embeddings: 'Embeddings',
    retrieval: 'Retrieval',
    chunking: 'Chunking',
    apiWaiting: 'Aguardando API.',
    defaultTitle: 'Documento de demonstração',
    defaultQuestion: 'Como este projeto permite conversar com documentos privados localmente?',
    createError: 'Falha ao adicionar texto à base.',
    uploadError: 'Falha ao adicionar arquivo.',
    chatError: 'Falha ao conversar com a base local.',
    deleteError: 'Falha ao remover documento.',
    apiError: 'Falha ao conectar na API.',
    runtimeError: 'Falha ao testar o runtime local de IA.',
  },
} satisfies Record<Language, Record<string, unknown>>

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function parseOptionalNumber(value: string) {
  if (!value.trim()) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function hasMeaningfulCollectionChoice(collections: CollectionSummary[]) {
  return collections.length > 1
}

function uploadStatusKey(status: UploadStatus) {
  return status === 'idle' ? null : status
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

    return parsed
      .filter(isChatMessage)
      .map(({ id, role, content }) => ({ id, role, content }))
  } catch {
    return []
  }
}

function isFileDrag(event: DragEvent) {
  return Array.from(event.dataTransfer?.types ?? []).includes('Files')
}

function buildConversationContext(messages: ChatMessage[]): ConversationContextMessage[] {
  const recentMessages = messages.slice(-6).map(({ role, content }) => ({ role, content }))
  const context: ConversationContextMessage[] = []
  let totalLength = 0
  for (const message of [...recentMessages].reverse()) {
    if (totalLength + message.content.length > 3800) break
    context.unshift(message)
    totalLength += message.content.length
  }
  return context
}

function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [theme, setTheme] = useState<Theme>('light')
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [runtimeConfig, setRuntimeConfig] = useState<RuntimeConfig | null>(null)
  const [runtimeProfile, setRuntimeProfile] = useState<RuntimeProfileName>('balanced')
  const [runtimeOptions, setRuntimeOptions] = useState<RuntimeOptions>(fallbackRuntimeProfiles.balanced)
  const [runtimeTestResult, setRuntimeTestResult] = useState<RuntimeTestResponse | null>(null)
  const [collections, setCollections] = useState<CollectionSummary[]>([])
  const [activeCollectionId, setActiveCollectionId] = useState<string | null>(null)
  const [indexStatus, setIndexStatus] = useState<IndexStatusResponse | null>(null)
  const [title, setTitle] = useState(copy.en.defaultTitle as string)
  const [content, setContent] = useState(sampleDocuments.en)
  const [question, setQuestion] = useState(copy.en.defaultQuestion as string)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(readPersistedChatMessages)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle')
  const [isPasteModalOpen, setIsPasteModalOpen] = useState(false)
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isTestingRuntime, setIsTestingRuntime] = useState(false)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { documents, refreshDocuments, removeDocument } = useDocuments()

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
      if (droppedFile) {
        setSelectedFile(droppedFile)
        setUploadStatus('selected')
      }
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
      const persistedMessages = chatMessages.map(({ id, role, content }) => ({ id, role, content }))
      window.localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(persistedMessages))
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

  async function refreshIndexStatus() {
    setIndexStatus(await getIndexStatus())
  }
  useEffect(() => {
    async function boot() {
      try {
        const [publicConfig, localRuntimeConfig] = await Promise.all([getConfig(), getRuntimeConfig()])
        setConfig(publicConfig)
        setRuntimeConfig(localRuntimeConfig)
        setRuntimeOptions(localRuntimeConfig.default_options)
        setRuntimeProfile((localRuntimeConfig.default_options.profile as RuntimeProfileName) ?? 'balanced')
        const [_, collectionRecords, currentIndexStatus] = await Promise.all([
          refreshDocuments(),
          getCollections(),
          getIndexStatus(),
        ])
        setCollections(collectionRecords)
        setIndexStatus(currentIndexStatus)
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

  function applyRuntimeProfile(profile: RuntimeProfileName) {
    const configuredProfile = runtimeConfig?.profiles?.[profile]
    const fallbackProfile = fallbackRuntimeProfiles[profile]
    setRuntimeProfile(profile)
    setRuntimeOptions({ ...(configuredProfile ?? fallbackProfile), profile })
    setRuntimeTestResult(null)
  }

  function updateRuntimeOption<Key extends keyof RuntimeOptions>(key: Key, value: RuntimeOptions[Key]) {
    setRuntimeProfile('custom')
    setRuntimeOptions((currentOptions) => ({ ...currentOptions, profile: 'custom', [key]: value }))
    setRuntimeTestResult(null)
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
      await refreshIndexStatus()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (t.createError as string))
    } finally {
      setIsLoading(false)
    }
  }

  async function handleUploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedFile) return
    setUploadStatus('uploading')
    setError(null)
    try {
      await uploadDocument(selectedFile)
      setSelectedFile(null)
      setUploadStatus('ready')
      await refreshDocuments()
      await refreshIndexStatus()
    } catch (caught) {
      setUploadStatus('error')
      setError(caught instanceof Error ? caught.message : (t.uploadError as string))
    } finally {
      setUploadStatus((currentStatus) => (currentStatus === 'uploading' ? 'error' : currentStatus))
    }
  }

  async function handleRuntimeTest() {
    setIsTestingRuntime(true)
    setError(null)
    setRuntimeTestResult(null)
    try {
      const result = await testRuntime(runtimeOptions)
      setRuntimeTestResult(result)
      if (!result.success && result.error) setError(result.error)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (t.runtimeError as string))
    } finally {
      setIsTestingRuntime(false)
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
        submittedQuestion,
        buildConversationContext(priorMessages),
        runtimeOptions,
        undefined,
        activeCollectionId,
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

  async function handleClearChat() {
    setError(null)
    try {
      await clearChatHistory()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (t.chatError as string))
    } finally {
      setChatMessages([])
    }
  }

  async function handleResetIndex() {
    if (!window.confirm(t.resetIndexConfirm as string)) return
    setIsLoading(true)
    setError(null)
    try {
      await resetIndex()
      setChatMessages([])
      await refreshDocuments()
      await refreshIndexStatus()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (t.deleteError as string))
    } finally {
      setIsLoading(false)
    }
  }

  async function handleCopyAnswer(messageId: string, answer: string) {
    try {
      await navigator.clipboard.writeText(answer)
      setCopiedMessageId(messageId)
      window.setTimeout(() => setCopiedMessageId(null), 1800)
    } catch {
      setError(t.chatError as string)
    }
  }

  async function handleDeleteDocument(documentId: string) {
    setIsLoading(true)
    setError(null)
    try {
      await removeDocument(documentId)
      setChatMessages([])
      await refreshIndexStatus()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (t.deleteError as string))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t.skipMain as string}
      </a>
      <main id="main-content" className="app-shell" data-theme={theme}>
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
              {theme === 'light' ? (t.darkTheme as string) : (t.lightTheme as string)}
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
            <p className={`upload-status ${uploadStatus}`} role="status">
              {uploadStatusKey(uploadStatus) === 'selected' && (t.uploadSelected as string)}
              {uploadStatusKey(uploadStatus) === 'uploading' && (t.uploadIndexing as string)}
              {uploadStatusKey(uploadStatus) === 'ready' && (t.uploadReady as string)}
              {uploadStatusKey(uploadStatus) === 'error' && (t.uploadFailed as string)}
            </p>
          </div>
          {selectedFile ? (
            <button className="action-button" disabled={uploadStatus === 'uploading'} type="submit">
              {uploadStatus === 'uploading' ? (t.uploadIndexing as string) : (t.addFileToBase as string)}
            </button>
          ) : (
            <label className="action-button file-action-button" aria-disabled={uploadStatus === 'uploading'}>
              {t.chooseLocalFile as string}
              <input
                type="file"
                accept=".txt,.md,.markdown,.pdf,.docx,.pptx,.xlsx,.png,.jpg,.jpeg,.tif,.tiff"
                disabled={uploadStatus === 'uploading'}
                onChange={(event) => {
                  const file = event.target.files?.[0] ?? null
                  setSelectedFile(file)
                  setUploadStatus(file ? 'selected' : 'idle')
                }}
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
                      {(t.chunkCount as (count: number) => string)(document.total_chunks)} ·{' '}
                      {(t.characterCount as (count: number) => string)(document.total_chars)} ·{' '}
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
            <div className="chat-heading-actions">
              {hasMeaningfulCollectionChoice(collections) && (
                <label className="collection-selector compact">
                  <span>{t.collections as string}</span>
                  <select
                    aria-label={t.collections as string}
                    value={activeCollectionId ?? ''}
                    onChange={(event) => {
                      setActiveCollectionId(event.target.value || null)
                      setChatMessages([])
                    }}
                  >
                    <option value="">{t.allCollections as string}</option>
                    {collections.map((collection) => (
                      <option key={collection.id} value={collection.id}>
                        {collection.name} · {(t.activeSources as (count: number) => string)(collection.active_sources)}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {hasChatMessages && (
                <button className="ghost" onClick={() => void handleClearChat()} type="button">
                  {t.clearChat as string}
                </button>
              )}
            </div>
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
                    <span>{message.response.retrieval_mode}</span>
                    <span>{message.response.latency_ms} ms</span>
                    <button
                      className="ghost"
                      onClick={() => void handleCopyAnswer(message.id, message.content)}
                      type="button"
                    >
                      {copiedMessageId === message.id ? t.copied : t.copyAnswer}
                    </button>
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
                      {message.response.sources.map((source, sourceIndex) => (
                        <SourceCard
                          key={`${message.id}-${source.chunk_id}`}
                          source={source}
                          sourceIndex={sourceIndex}
                          language={language}
                        />
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

      <section className="card stack runtime-card">
        <div className="chat-heading">
          <div>
            <p className="eyebrow">{t.runtimeSettings as string}</p>
            <h2>{t.runtimeProfile as string}</h2>
            <p className="muted">{t.runtimeSettingsText as string}</p>
          </div>
          <button disabled={isTestingRuntime || !runtimeConfig} onClick={() => void handleRuntimeTest()} type="button">
            {isTestingRuntime ? (t.testingRuntime as string) : (t.testRuntime as string)}
          </button>
        </div>

        {runtimeConfig ? (
          <>
            <div className="runtime-profiles" role="group" aria-label={t.runtimeProfile as string}>
              {(['economy', 'balanced', 'strong', 'custom'] as RuntimeProfileName[]).map((profile) => (
                <button
                  className={runtimeProfile === profile ? 'runtime-profile active' : 'runtime-profile'}
                  key={profile}
                  onClick={() => applyRuntimeProfile(profile)}
                  type="button"
                >
                  {profile === 'economy' && (t.economyProfile as string)}
                  {profile === 'balanced' && (t.balancedProfile as string)}
                  {profile === 'strong' && (t.strongProfile as string)}
                  {profile === 'custom' && (t.customProfile as string)}
                </button>
              ))}
            </div>

            <div className="runtime-grid">
              <label>
                {t.model as string}
                <input
                  value={runtimeOptions.model ?? ''}
                  onChange={(event) => updateRuntimeOption('model', event.target.value)}
                />
              </label>
              <label>
                {t.contextWindow as string}
                <input
                  min={512}
                  step={512}
                  type="number"
                  value={runtimeOptions.num_ctx ?? ''}
                  onChange={(event) => updateRuntimeOption('num_ctx', parseOptionalNumber(event.target.value))}
                />
              </label>
              <label>
                {t.gpuLayers as string}
                <input
                  min={0}
                  placeholder={t.gpuAuto as string}
                  type="number"
                  value={runtimeOptions.num_gpu ?? ''}
                  onChange={(event) => updateRuntimeOption('num_gpu', parseOptionalNumber(event.target.value))}
                />
              </label>
              <label>
                {t.keepAlive as string}
                <input
                  value={runtimeOptions.keep_alive ?? ''}
                  onChange={(event) => updateRuntimeOption('keep_alive', event.target.value || null)}
                />
              </label>
              <label>
                {t.temperature as string}
                <input
                  max={2}
                  min={0}
                  step={0.1}
                  type="number"
                  value={runtimeOptions.temperature ?? ''}
                  onChange={(event) =>
                    updateRuntimeOption('temperature', parseOptionalNumber(event.target.value))
                  }
                />
              </label>
              <label>
                {t.thinkingSetting as string}
                <input
                  checked={runtimeOptions.think ?? false}
                  type="checkbox"
                  onChange={(event) => updateRuntimeOption('think', event.target.checked)}
                />
              </label>
            </div>

            <div className="runtime-summary">
              <span>{runtimeOptions.model || runtimeConfig.llm_model}</span>
              <span>ctx {runtimeOptions.num_ctx ?? (t.gpuAuto as string)}</span>
              <span>gpu {runtimeOptions.num_gpu ?? (t.gpuAuto as string)}</span>
              <span>{runtimeOptions.think ? (t.thinkingOn as string) : (t.thinkingOff as string)}</span>
              <span>{runtimeOptions.keep_alive || t.keepAliveAuto}</span>
            </div>

            {runtimeTestResult && (
              <div className={runtimeTestResult.success ? 'runtime-result success' : 'runtime-result failure'}>
                <strong>
                  {runtimeTestResult.success
                    ? (t.runtimeSuccess as string)
                    : (t.runtimeFailure as string)}
                </strong>
                <p>
                  {runtimeTestResult.model} · {runtimeTestResult.latency_ms} ms
                </p>
                {runtimeTestResult.answer && <p>{runtimeTestResult.answer}</p>}
                {runtimeTestResult.error && <p>{runtimeTestResult.error}</p>}
              </div>
            )}
          </>
        ) : (
          <p className="muted">{t.runtimeUnavailable as string}</p>
        )}
      </section>

      <section className="card config-card">
        <p className="eyebrow">{t.techStatus as string}</p>
        {indexStatus && (
          <div className={`index-health state-${indexStatus.state}`} aria-label="Index health">
            <div className="chat-heading">
              <div>
                <strong>{t.indexHealth as string}</strong>
                <p className="muted">
                  {indexStatus.state} · {(t.documentCount as (count: number) => string)(indexStatus.document_count)} ·{' '}
                  {(t.chunkCount as (count: number) => string)(indexStatus.chunk_count)}
                </p>
              </div>
              <button className="secondary" disabled={isLoading} onClick={() => void handleResetIndex()} type="button">
                {t.resetIndex as string}
              </button>
            </div>
            {indexStatus.reindex_required && indexStatus.reason && <p className="alert">{indexStatus.reason}</p>}
          </div>
        )}
        {config ? (
          <dl>
            <div>
              <dt>{t.llm as string}</dt>
              <dd>
                {config.llm_provider} · {runtimeOptions.model || config.llm_model}
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
                {(t.characterCount as (count: number) => string)(config.chunk_size)} · {t.overlap as string}{' '}
                {config.chunk_overlap}
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
    </>
  )
}

export default App
