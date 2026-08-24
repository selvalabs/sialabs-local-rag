from pathlib import Path


def test_scale_benchmark_declares_required_default_sizes() -> None:
    source = Path('benchmarks/retrieval_scale.py').read_text(encoding='utf-8')

    for size in ('1_000', '5_000', '10_000', '25_000', '50_000'):
        assert size in source
    assert 'cold_dense_ms' in source
    assert 'warm_hybrid_ms' in source
    assert 'database_bytes' in source
