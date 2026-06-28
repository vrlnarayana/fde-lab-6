from __future__ import annotations
from math import floor, ceil
from api.config import Settings
from api.models import BenchmarkRow


def percentile(sorted_vals: list[float], p: float) -> float:
    """Linear-interpolation percentile. Input need not be pre-sorted."""
    if not sorted_vals:
        return 0.0
    vals = sorted(sorted_vals)
    k = (len(vals) - 1) * (p / 100.0)
    f, c = floor(k), ceil(k)
    if f == c:
        return float(vals[int(k)])
    return vals[f] * (c - k) + vals[c] * (k - f)


def summarize(provider: str, latencies_ms: list[float], token_counts: list[int], model: str,
              settings: Settings, *, residency: str, auth: str, simulated: bool) -> BenchmarkRow:
    """Discard the warm-up (first) sample, then compute p50/p95, avg tokens, cost/1k calls."""
    lat = latencies_ms[1:] if len(latencies_ms) > 1 else latencies_ms
    tok = token_counts[1:] if len(token_counts) > 1 else token_counts
    avg_tokens = (sum(tok) / len(tok)) if tok else 0.0
    rate = settings.rate_per_1k_tokens.get(model, 0.0)
    return BenchmarkRow(
        provider=provider,
        p50_ms=round(percentile(lat, 50), 2),
        p95_ms=round(percentile(lat, 95), 2),
        avg_tokens=round(avg_tokens, 2),
        cost_per_1k_calls=round(avg_tokens * rate, 6),
        residency=residency,
        auth=auth,
        simulated=simulated,
    )


def synthetic_latencies(n: int, base_ms: float, step_ms: float) -> list[float]:
    """Deterministic illustrative latencies for offline mock-vs-mock (no randomness)."""
    return [round(base_ms + (i % 7) * step_ms, 2) for i in range(n)]


def recommend(rows: list[BenchmarkRow]) -> str:
    # Azure-wins verdict is an intentional fixed pedagogical narrative: residency is the deciding constraint by design, not data-driven.
    azure = next((r for r in rows if r.provider == "azure"), None)
    if azure is not None:
        return ("For Britannia, choose Azure OpenAI: the EU/UK residency + keyless identity "
                "envelope is the deciding constraint, and it wins even at latency/price parity.")
    return "Insufficient data — run the Azure row to make the residency/identity call."
