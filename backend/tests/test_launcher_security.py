from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LAUNCHER_PATH = _REPO_ROOT / "launcher" / "local_launcher.py"


def _launcher_namespace() -> dict[str, object]:
    return cast(dict[str, object], runpy.run_path(str(_LAUNCHER_PATH)))


def _mutation_guard() -> Callable[[str | None, str | None], bool]:
    namespace = _launcher_namespace()
    return cast(
        Callable[[str | None, str | None], bool],
        namespace["browser_mutation_is_trusted"],
    )


def test_launcher_default_bind_is_loopback() -> None:
    namespace = _launcher_namespace()
    assert namespace["HOST"] == "127.0.0.1"


def test_trusted_local_frontend_origin_can_mutate() -> None:
    guard = _mutation_guard()
    assert guard("http://127.0.0.1:4182", "same-site") is True
    assert guard("http://localhost:5173", "same-site") is True


def test_external_browser_origin_is_rejected() -> None:
    guard = _mutation_guard()
    assert guard("https://example.com", "cross-site") is False
    assert guard("https://example.com", None) is False


def test_cross_site_fetch_is_rejected_even_with_local_origin() -> None:
    guard = _mutation_guard()
    assert guard("http://127.0.0.1:4182", "cross-site") is False


def test_non_browser_local_automation_remains_supported() -> None:
    guard = _mutation_guard()
    assert guard(None, None) is True
