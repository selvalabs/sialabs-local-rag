from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import time
import tracemalloc
from pathlib import Path
from tempfile import TemporaryDirectory

from sialabs_local_rag.database import Database
from sialabs_local_rag.providers import HashEmbeddingProvider
from sialabs_local_rag.retrieval import RetrievalOptions, retrieve_sources
from sialabs_local_rag.storage import ChunkInput, Storage

DEFAULT_SIZES = (1_000, 5_000, 10_000, 25_000, 50_000)


async def benchmark_size(size: int) -> dict[str, float | int]:
    provider = HashEmbeddingProvider()
    with TemporaryDirectory(prefix=f'sialabs-rag-benchmark-{size}-') as temp_dir:
        database_path = Path(temp_dir) / 'benchmark.db'
        database = Database(f'sqlite:///{database_path}')
        database.init_schema()
        storage = Storage(database)
        texts = [
            f'Synthetic benchmark chunk {index}. '
            f'The local retrieval corpus contains token-{index % 997}.'
            for index in range(size)
        ]

        started = time.perf_counter()
        embeddings = await provider.embed(texts)
        chunks = [
            ChunkInput(index=index, content=text, embedding=embeddings[index])
            for index, text in enumerate(texts)
        ]
        storage.create_document(
            title=f'Benchmark {size}',
            source_type='benchmark',
            original_content='\n\n'.join(texts),
            chunks=chunks,
            embedding_provider=provider.name,
            embedding_model=provider.model,
        )
        ingest_ms = (time.perf_counter() - started) * 1000

        query_text = 'Which synthetic chunk contains token-421?'
        started = time.perf_counter()
        query_embedding = (await provider.embed([query_text]))[0]
        query_embedding_ms = (time.perf_counter() - started) * 1000

        def run(mode: str) -> float:
            started_at = time.perf_counter()
            retrieve_sources(
                storage=storage,
                query_text=query_text,
                query_embedding=query_embedding,
                top_k=5,
                embedding_provider=provider.name,
                embedding_model=provider.model,
                options=RetrievalOptions(mode=mode),
            )
            return (time.perf_counter() - started_at) * 1000

        tracemalloc.start()
        cold_dense_ms = run('dense')
        warm_dense_ms = run('dense')
        warm_hybrid_ms = run('hybrid')
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            'chunks': size,
            'ingest_ms': round(ingest_ms, 2),
            'database_bytes': database_path.stat().st_size,
            'query_embedding_ms': round(query_embedding_ms, 2),
            'cold_dense_ms': round(cold_dense_ms, 2),
            'warm_dense_ms': round(warm_dense_ms, 2),
            'warm_hybrid_ms': round(warm_hybrid_ms, 2),
            'retrieval_peak_traced_bytes': peak_bytes,
        }


async def run(sizes: tuple[int, ...]) -> dict[str, object]:
    return {
        'benchmark': 'local-rag-retrieval-scale',
        'embedding_provider': 'hash',
        'metadata': {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'processor': platform.processor() or 'unknown',
            'cpu_count': os.cpu_count(),
        },
        'sizes': [await benchmark_size(size) for size in sizes],
        'limitations': [
            'Synthetic corpus and hash embeddings are regression inputs, not production workloads.',
            'Results are machine-specific and do not establish a universal latency SLO.',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Benchmark local retrieval at increasing corpus sizes.'
    )
    parser.add_argument('--sizes', nargs='+', type=int, default=DEFAULT_SIZES)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = asyncio.run(run(tuple(args.sizes)))
    payload = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8')
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
