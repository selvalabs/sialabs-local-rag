from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (_REPO_ROOT / path).read_text(encoding="utf-8-sig")


def test_windows_setup_prepares_backend_frontend_and_shortcut() -> None:
    setup = _read("scripts/install-windows-app.ps1")

    assert "Assert-PythonAvailable" in setup
    assert 'Invoke-NativeChecked "backend dependency sync" "uv" @("sync")' in setup
    assert 'Invoke-NativeChecked "frontend production build" "npm" @("run", "build")' in setup
    assert "Assert-FrontendBuildExists" in setup
    assert "create-desktop-shortcut.ps1" in setup


def test_skip_frontend_build_requires_existing_artifact() -> None:
    setup = _read("scripts/install-windows-app.ps1")

    assert "if ($SkipFrontendBuild)" in setup
    assert "Assert-FrontendBuildExists" in setup
    assert "Frontend build is missing" in setup


def test_desktop_shortcut_targets_one_click_startup_script() -> None:
    shortcut = _read("scripts/create-desktop-shortcut.ps1")

    assert '"start-local-app.ps1"' in shortcut
    assert "-WindowStyle Hidden" in shortcut
    assert 'Shortcut.Description = "Start SIALabs Local RAG"' in shortcut


def test_startup_script_runs_launcher_backend_and_local_frontend() -> None:
    startup = _read("scripts/start-local-app.ps1")

    assert '"start-launcher.ps1"' in startup
    assert '"$LauncherUrl/backend/start"' in startup
    assert 'FrontendPort = 4182' in startup
    assert "http.server $FrontendPort --bind 127.0.0.1" in startup
    assert "Start-Process $FrontendUrl" in startup


def test_frontend_mounts_launcher_control_panel() -> None:
    main = _read("frontend/src/main.tsx")
    panel = _read("frontend/src/LauncherPanel.tsx")

    assert "import { LauncherPanel }" in main
    assert "<LauncherPanel />" in main
    assert "startLauncherBackend" in panel
    assert "restartLauncherBackend" in panel
    assert "stopLauncherBackend" in panel
    assert "getLauncherBackendLogs" in panel


def test_windows_docs_keep_ollama_and_models_external() -> None:
    docs = _read("installer/windows/README.md")

    assert "Ollama" in docs
    assert "external" in docs.casefold()
    assert "gemma4:e2b" in docs
    assert "embeddinggemma" in docs
