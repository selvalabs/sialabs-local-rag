const LAUNCHER_URL = import.meta.env.VITE_LAUNCHER_URL ?? 'http://127.0.0.1:8765'
const LAUNCHER_TOKEN = import.meta.env.VITE_LAUNCHER_TOKEN as string | undefined

export type LauncherHealth = {
  online: boolean
  status_code: number | null
  latency_ms: number
  error: string | null
}

export type LauncherBackendProcess = {
  managed: boolean
  stale_process?: boolean
  running: boolean
  pid: number | null
  return_code: number | null
}

export type LauncherStatus = {
  launcher: {
    online: boolean
    host: string
    port: number
    repo_root: string
    backend_dir: string
    token_required: boolean
  }
  backend: {
    url: string
    health: LauncherHealth
    process: LauncherBackendProcess
  }
  ollama: {
    url: string
    health: LauncherHealth
  }
}

export type LauncherActionResponse = Record<string, unknown>

export type BackendLogsResponse = {
  lines: string[]
}

function launcherHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (LAUNCHER_TOKEN) {
    headers['X-SIALabs-Launcher-Token'] = LAUNCHER_TOKEN
  }
  return headers
}

async function fetchLauncher(input: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${LAUNCHER_URL}${input}`, init)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Could not reach the local launcher at ${LAUNCHER_URL}. Start the launcher and try again.`,
      )
    }
    throw error
  }
}

async function parseLauncherResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Launcher request failed with status ${response.status}`
    try {
      const errorBody = (await response.json()) as { error?: unknown; detail?: unknown }
      if (typeof errorBody.error === 'string') detail = errorBody.error
      if (typeof errorBody.detail === 'string') detail = errorBody.detail
    } catch {
      // Preserve default message when body is not JSON.
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

export async function getLauncherStatus(): Promise<LauncherStatus> {
  const response = await fetchLauncher('/status')
  return parseLauncherResponse<LauncherStatus>(response)
}

async function postLauncherAction(path: string): Promise<LauncherActionResponse> {
  const response = await fetchLauncher(path, {
    method: 'POST',
    headers: launcherHeaders(),
    body: JSON.stringify({}),
  })
  return parseLauncherResponse<LauncherActionResponse>(response)
}

export async function startLauncherBackend(): Promise<LauncherActionResponse> {
  return postLauncherAction('/backend/start')
}

export async function stopLauncherBackend(): Promise<LauncherActionResponse> {
  return postLauncherAction('/backend/stop')
}

export async function restartLauncherBackend(): Promise<LauncherActionResponse> {
  return postLauncherAction('/backend/restart')
}

export async function getLauncherBackendLogs(): Promise<string[]> {
  const response = await fetchLauncher('/logs/backend')
  const body = await parseLauncherResponse<BackendLogsResponse>(response)
  return body.lines
}
