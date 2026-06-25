from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HOST = os.environ.get("SIALABS_LAUNCHER_HOST", "127.0.0.1")
PORT = int(os.environ.get("SIALABS_LAUNCHER_PORT", "8765"))
TOKEN = os.environ.get("SIALABS_LAUNCHER_TOKEN")

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(os.environ.get("SIALABS_BACKEND_DIR", REPO_ROOT / "backend"))
BACKEND_URL = os.environ.get("SIALABS_BACKEND_URL", "http://127.0.0.1:8000")
OLLAMA_URL = os.environ.get("SIALABS_OLLAMA_URL", "http://127.0.0.1:11434")

DEFAULT_BACKEND_ARGS = [
    "-m",
    "uvicorn",
    "sialabs_local_rag.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
]

LOCAL_FRONTEND_ORIGINS = {
    "http://127.0.0.1:4173",
    "http://127.0.0.1:4181",
    "http://127.0.0.1:4182",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://localhost:4181",
    "http://localhost:4182",
    "http://localhost:5173",
}

BACKEND_CORS_ORIGINS = ",".join(sorted(LOCAL_FRONTEND_ORIGINS))
backend_process: subprocess.Popen[str] | None = None
backend_log: deque[str] = deque(maxlen=500)
backend_lock = threading.Lock()


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length") or 0)
    if length <= 0:
        return {}
    raw_body = handler.rfile.read(length)
    return json.loads(raw_body.decode("utf-8"))


def check_http(url: str, timeout: float = 1.5) -> dict[str, Any]:
    request = Request(url, method="GET")
    started_at = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            return {
                "online": 200 <= response.status < 500,
                "status_code": response.status,
                "latency_ms": latency_ms,
                "error": None,
            }
    except HTTPError as exc:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "online": True,
            "status_code": exc.code,
            "latency_ms": latency_ms,
            "error": str(exc),
        }
    except (TimeoutError, URLError, OSError) as exc:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "online": False,
            "status_code": None,
            "latency_ms": latency_ms,
            "error": str(exc),
        }


def backend_python_path() -> Path | None:
    candidates = [
        BACKEND_DIR / ".venv" / "Scripts" / "python.exe",
        BACKEND_DIR / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def backend_command() -> list[str]:
    configured_command = os.environ.get("SIALABS_BACKEND_COMMAND")
    if configured_command:
        return shlex.split(configured_command, posix=os.name != "nt")

    backend_python = backend_python_path()
    if backend_python:
        return [str(backend_python), *DEFAULT_BACKEND_ARGS]

    return ["uv", "run", "python", *DEFAULT_BACKEND_ARGS]


def backend_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("LLM_PROVIDER", "ollama")
    env.setdefault("EMBEDDING_PROVIDER", "ollama")
    env.setdefault("OLLAMA_BASE_URL", OLLAMA_URL)
    env.setdefault("OLLAMA_CHAT_MODEL", "gemma4:e2b")
    env.setdefault("OLLAMA_EMBED_MODEL", "embeddinggemma")
    env.setdefault("OLLAMA_NUM_CTX", "4096")
    env.setdefault("OLLAMA_TEMPERATURE", "0.2")
    env.setdefault("OLLAMA_KEEP_ALIVE", "5m")
    env.setdefault("CORS_ORIGINS", BACKEND_CORS_ORIGINS)
    return env


def stream_backend_logs(process: subprocess.Popen[str]) -> None:
    if process.stdout is None:
        return
    for line in process.stdout:
        backend_log.append(line.rstrip())


def process_is_running(process: subprocess.Popen[str] | None) -> bool:
    return process is not None and process.poll() is None


def backend_is_reachable() -> bool:
    return bool(check_http(f"{BACKEND_URL}/api/config", timeout=0.5)["online"])


def wait_until_backend_offline(timeout_seconds: float = 8.0) -> bool:
    deadline = time.perf_counter() + timeout_seconds
    while time.perf_counter() < deadline:
        if not backend_is_reachable():
            return True
        time.sleep(0.35)
    return False


def managed_backend_status() -> dict[str, Any]:
    with backend_lock:
        running = process_is_running(backend_process)
        return {
            "managed": running,
            "stale_process": backend_process is not None and not running,
            "running": running,
            "pid": backend_process.pid if running and backend_process else None,
            "return_code": backend_process.poll() if backend_process else None,
        }


def start_backend() -> dict[str, Any]:
    global backend_process
    with backend_lock:
        if process_is_running(backend_process):
            return {"started": False, "reason": "managed backend already running"}

        if backend_process is not None and backend_process.poll() is not None:
            backend_process = None

        if backend_is_reachable():
            return {"started": False, "reason": "backend already reachable", "managed": False}

        command = backend_command()
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        backend_log.append(f"$ {' '.join(command)}")
        backend_process = subprocess.Popen(
            command,
            cwd=BACKEND_DIR,
            env=backend_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )
        threading.Thread(
            target=stream_backend_logs,
            args=(backend_process,),
            daemon=True,
        ).start()
        return {"started": True, "pid": backend_process.pid, "command": command}


def stop_backend() -> dict[str, Any]:
    global backend_process
    with backend_lock:
        if not process_is_running(backend_process):
            if backend_process is not None and backend_process.poll() is not None:
                backend_process = None
            return {"stopped": False, "reason": "no managed backend running"}

        assert backend_process is not None
        process = backend_process
        pid = process.pid
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        return_code = process.returncode
        backend_process = None

    stopped = wait_until_backend_offline()
    return {"stopped": stopped, "pid": pid, "return_code": return_code}


def restart_backend() -> dict[str, Any]:
    stop_result = stop_backend()
    if stop_result.get("stopped") is False and backend_is_reachable():
        return {
            "stop": stop_result,
            "start": {
                "started": False,
                "reason": "backend is still reachable after stop",
            },
        }
    start_result = start_backend()
    return {"stop": stop_result, "start": start_result}


def launcher_status() -> dict[str, Any]:
    return {
        "launcher": {
            "online": True,
            "host": HOST,
            "port": PORT,
            "repo_root": str(REPO_ROOT),
            "backend_dir": str(BACKEND_DIR),
            "token_required": bool(TOKEN),
        },
        "backend": {
            "url": BACKEND_URL,
            "health": check_http(f"{BACKEND_URL}/api/config"),
            "process": managed_backend_status(),
        },
        "ollama": {
            "url": OLLAMA_URL,
            "health": check_http(f"{OLLAMA_URL}/api/tags"),
        },
    }


class LauncherHandler(BaseHTTPRequestHandler):
    server_version = "SIALabsLocalLauncher/0.1"

    def end_headers(self) -> None:
        origin = self.headers.get("origin")
        if origin in LOCAL_FRONTEND_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-SIALabs-Launcher-Token")
        super().end_headers()

    def send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json_bytes(payload)
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def token_is_valid(self) -> bool:
        if not TOKEN:
            return True
        return self.headers.get("X-SIALabs-Launcher-Token") == TOKEN

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_json(200, {"ok": True})
            return
        if self.path == "/status":
            self.send_json(200, launcher_status())
            return
        if self.path == "/logs/backend":
            self.send_json(200, {"lines": list(backend_log)})
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self.token_is_valid():
            self.send_json(401, {"error": "invalid launcher token"})
            return

        try:
            read_json_body(self)
        except json.JSONDecodeError as exc:
            self.send_json(400, {"error": f"invalid JSON body: {exc}"})
            return

        if self.path == "/backend/start":
            self.send_json(200, start_backend())
            return
        if self.path == "/backend/stop":
            self.send_json(200, stop_backend())
            return
        if self.path == "/backend/restart":
            self.send_json(200, restart_backend())
            return
        self.send_json(404, {"error": "not found"})

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("launcher: " + format % args + "\n")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), LauncherHandler)
    print(f"SIALabs Local Launcher listening at http://{HOST}:{PORT}")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Backend directory: {BACKEND_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
