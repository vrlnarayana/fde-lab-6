from api.benchmark import percentile, summarize, synthetic_latencies, recommend
from api.config import Settings

def test_percentile_interpolates():
    vals = [20.0, 30.0, 40.0, 50.0]
    assert percentile(vals, 50) == 35.0
    assert abs(percentile(vals, 95) - 48.5) < 1e-9

def test_percentile_empty_is_zero():
    assert percentile([], 50) == 0.0

def test_summarize_discards_warmup_and_costs():
    s = Settings(azure_openai_endpoint=None)
    row = summarize("azure", [999.0, 20.0, 30.0, 40.0, 50.0], [0, 50, 50, 50, 50],
                    model="gpt-4o-mini", settings=s, residency="EU/UK", auth="keyless", simulated=True)
    # warm-up (999/0) dropped -> latencies [20,30,40,50], tokens avg 50
    assert row.p50_ms == 35.0
    assert row.avg_tokens == 50.0
    assert abs(row.cost_per_1k_calls - 50 * 0.0006) < 1e-9
    assert row.simulated is True

def test_synthetic_latencies_deterministic():
    a = synthetic_latencies(5, base_ms=100.0, step_ms=5.0)
    b = synthetic_latencies(5, base_ms=100.0, step_ms=5.0)
    assert a == b
    assert len(a) == 5

def test_recommend_mentions_residency():
    s = Settings()
    rows = [summarize("azure", [10, 20], [10, 10], "gpt-4o-mini", s,
                      residency="EU/UK", auth="keyless", simulated=True)]
    assert "residency" in recommend(rows).lower() or "eu/uk" in recommend(rows).lower()
