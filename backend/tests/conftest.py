from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sialabs_local_rag.main import create_app
from sialabs_local_rag.settings import Settings


@pytest.fixture()
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    settings = Settings(
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        llm_provider="mock",
        embedding_provider="hash",
        chunk_size=400,
        chunk_overlap=60,
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
