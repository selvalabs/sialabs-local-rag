from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_repo_file(path: str) -> str:
    return (_REPO_ROOT / path).read_text(encoding="utf-8-sig")


def test_release_preflight_runs_deterministic_dense_and_hybrid_evaluation() -> None:
    script = _read_repo_file("scripts/release-preflight.ps1")

    assert 'Invoke-DeterministicEvaluation "dense"' in script
    assert 'Invoke-DeterministicEvaluation "hybrid"' in script
    assert '"--provider",' in script
    assert '"hash",' in script


def test_release_preflight_requires_clean_synchronized_tagged_main() -> None:
    script = _read_repo_file("scripts/release-preflight.ps1")

    assert script.count("Assert-CleanGitTree") >= 3
    assert "Assert-MainBranch" in script
    assert "Assert-MainSynchronized" in script
    assert '"fetch", "origin", "main", "--tags", "--quiet"' in script
    assert "Assert-VersionTagPointsToHead" in script


def test_packaging_docs_reference_release_readiness_gate() -> None:
    installers = _read_repo_file("docs/INSTALLERS.md")
    windows = _read_repo_file("installer/windows/README.md")
    readiness = _read_repo_file("docs/RELEASE_READINESS.md")

    assert "RELEASE_READINESS.md" in installers
    assert "RELEASE_READINESS.md" in windows
    assert "#52" in readiness
    assert "#54" in readiness
    assert "#55" in readiness
    assert "#53" in readiness
    assert "#49" in readiness
