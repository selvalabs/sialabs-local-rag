import { useEffect, useState } from 'react'

import {
  getLauncherBackendLogs,
  getLauncherStatus,
  restartLauncherBackend,
  startLauncherBackend,
  stopLauncherBackend,
} from './launcherApi'
import type { LauncherActionResponse, LauncherHealth, LauncherStatus } from './launcherApi'

const STATUS_REFRESH_MS = 5000

function getErrorMessage(caught: unknown, fallback: string) {
  return caught instanceof Error ? caught.message : fallback
}

function healthText(health?: LauncherHealth) {
  if (!health) return 'desconhecido'
  return health.online ? `online · ${health.latency_ms} ms` : 'offline'
}

function processText(status: LauncherStatus | null) {
  if (!status) return 'sem status'
  const process = status.backend.process
  if (process.running && process.pid) return `gerenciado · PID ${process.pid}`
  if (status.backend.health.online) return 'online fora do controle do launcher'
  if (process.stale_process) return 'processo anterior encerrado'
  return 'parado'
}

function serviceClassName(online?: boolean) {
  return online ? 'launcher-service online' : 'launcher-service offline'
}

function stringifyActionResult(result: LauncherActionResponse) {
  return JSON.stringify(result, null, 2)
}

export function LauncherPanel() {
  const [status, setStatus] = useState<LauncherStatus | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [lastAction, setLastAction] = useState<string | null>(null)
  const [isBusy, setIsBusy] = useState(false)
  const [showLogs, setShowLogs] = useState(false)

  async function refreshStatus(options: { quiet?: boolean } = {}) {
    try {
      const nextStatus = await getLauncherStatus()
      setStatus(nextStatus)
      if (!options.quiet) setError(null)
    } catch (caught) {
      setStatus(null)
      if (!options.quiet) {
        setError(getErrorMessage(caught, 'Falha ao conectar ao launcher local.'))
      }
    }
  }

  async function refreshLogs() {
    try {
      const nextLogs = await getLauncherBackendLogs()
      setLogs(nextLogs)
      setShowLogs(true)
    } catch (caught) {
      setError(getErrorMessage(caught, 'Falha ao carregar logs do backend.'))
    }
  }

  async function runBackendAction(action: () => Promise<LauncherActionResponse>) {
    setIsBusy(true)
    setError(null)
    try {
      const result = await action()
      setLastAction(stringifyActionResult(result))
      await refreshStatus({ quiet: true })
      await refreshLogs()
    } catch (caught) {
      setError(getErrorMessage(caught, 'Falha ao executar ação do launcher.'))
    } finally {
      setIsBusy(false)
    }
  }

  useEffect(() => {
    void refreshStatus()
    const interval = window.setInterval(() => {
      void refreshStatus({ quiet: true })
    }, STATUS_REFRESH_MS)
    return () => window.clearInterval(interval)
  }, [])

  return (
    <section className="card stack launcher-card standalone-launcher-panel">
      <div className="chat-heading">
        <div>
          <p className="eyebrow">Runtime launcher</p>
          <h2>Controle local</h2>
          <p className="muted">
            Inicie, reinicie e acompanhe o backend local sem abrir outro terminal para o servidor.
          </p>
        </div>
        <button className="ghost" disabled={isBusy} onClick={() => void refreshStatus()} type="button">
          Atualizar
        </button>
      </div>

      {error && <div className="alert">{error}</div>}

      <div className="launcher-status-grid">
        <article className={serviceClassName(status?.launcher.online)}>
          <span className="launcher-dot" />
          <div>
            <strong>Launcher</strong>
            <p>{status ? `${status.launcher.host}:${status.launcher.port}` : 'offline'}</p>
          </div>
        </article>
        <article className={serviceClassName(status?.backend.health.online)}>
          <span className="launcher-dot" />
          <div>
            <strong>Backend</strong>
            <p>{healthText(status?.backend.health)}</p>
            <small>{processText(status)}</small>
          </div>
        </article>
        <article className={serviceClassName(status?.ollama.health.online)}>
          <span className="launcher-dot" />
          <div>
            <strong>Ollama</strong>
            <p>{healthText(status?.ollama.health)}</p>
            <small>{status?.ollama.url ?? 'http://127.0.0.1:11434'}</small>
          </div>
        </article>
      </div>

      <div className="launcher-actions">
        <button
          disabled={isBusy}
          onClick={() => void runBackendAction(startLauncherBackend)}
          type="button"
        >
          Start backend
        </button>
        <button
          className="secondary"
          disabled={isBusy}
          onClick={() => void runBackendAction(restartLauncherBackend)}
          type="button"
        >
          Restart backend
        </button>
        <button
          className="ghost"
          disabled={isBusy}
          onClick={() => void runBackendAction(stopLauncherBackend)}
          type="button"
        >
          Stop backend
        </button>
        <button className="ghost" disabled={isBusy} onClick={() => void refreshLogs()} type="button">
          Ver logs
        </button>
      </div>

      {lastAction && (
        <details className="launcher-action-result">
          <summary>Última ação</summary>
          <pre>{lastAction}</pre>
        </details>
      )}

      {showLogs && (
        <details className="launcher-log-block" open>
          <summary>Logs do backend</summary>
          <pre className="launcher-log">{logs.length > 0 ? logs.join('\n') : 'Sem logs ainda.'}</pre>
        </details>
      )}
    </section>
  )
}
