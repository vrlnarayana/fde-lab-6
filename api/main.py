from __future__ import annotations
import asyncio
from fastapi import FastAPI, HTTPException
from api.client import resilient_triage
from api.config import settings
from api.errors import ErrorEnvelope, ProviderError, TransientError
from api.models import TriageRequest, TriageResponse, BenchmarkRequest, BenchmarkRow
from api.triage import parse_triage
from api.providers import available_providers, make_provider, auth_posture
from api.benchmark import summarize, synthetic_latencies, recommend

app = FastAPI(title="Azure Labs 6-A/6-B — Britannia Dispute-Triage Copilot", version="0.1.0")

CHAT_MAX_RETRIES = 3


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/providers")
async def providers() -> dict:
    return {
        "providers": available_providers(settings),
        "default": settings.default_provider,
        "posture": auth_posture(settings),
    }


@app.get("/authcheck")
async def authcheck() -> dict:
    post = auth_posture(settings)
    return {
        **post,
        "checklist": {
            "resident_region": post["region"] in ("westeurope", "uksouth"),
            "keyless": post["mode"] == "keyless",
            "local_auth_disabled": post["disable_local_auth"],
            "no_secrets_in_use": not post["secrets_present"],
        },
    }


@app.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest) -> TriageResponse:
    try:
        provider = make_provider(
            request.provider or settings.default_provider, settings,
            fail_first_k=request.fail_first_k, force_bad_output=request.force_bad_output,
        )
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=ErrorEnvelope(
            error_type="ProviderError", message=str(exc), retryable=False).model_dump())

    try:
        outcome = await resilient_triage(provider, request, max_retries=CHAT_MAX_RETRIES, base_delay=0.05)
    except TransientError as exc:
        raise HTTPException(status_code=502, detail=ErrorEnvelope(
            error_type="TransientError", message=str(exc), retryable=True,
            attempts=CHAT_MAX_RETRIES + 1).model_dump())
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=ErrorEnvelope(
            error_type="TimeoutError", message="provider timed out", retryable=True).model_dump())

    triage_obj, error = parse_triage(outcome.raw.content)
    return TriageResponse(
        provider=provider.name,
        model=outcome.raw.model,
        auth_mode=getattr(provider, "auth_mode", "n/a"),
        attempts=outcome.attempts,
        latency_ms=round(outcome.latency_ms, 2),
        validated=triage_obj is not None,
        triage=triage_obj,
        error=error,
    )


@app.post("/benchmark")
async def benchmark(request: BenchmarkRequest) -> dict:
    rows: list[BenchmarkRow] = []
    for name in request.providers:
        try:
            provider = make_provider(name, settings)
        except ProviderError as exc:
            raise HTTPException(status_code=400, detail=ErrorEnvelope(
                error_type="ProviderError", message=str(exc), retryable=False).model_dump())

        latencies: list[float] = []
        tokens: list[int] = []
        try:
            if provider.is_mock:
                # Offline: deterministic illustrative latencies (clearly simulated).
                latencies = synthetic_latencies(request.n, base_ms=180.0, step_ms=12.0)
                for _ in range(request.n):
                    outcome = await resilient_triage(provider, TriageRequest(dispute_text=request.dispute_text), base_delay=0.001)
                    tokens.append(outcome.raw.usage.total)
            else:
                for _ in range(request.n):
                    outcome = await resilient_triage(provider, TriageRequest(dispute_text=request.dispute_text), base_delay=0.05)
                    latencies.append(outcome.latency_ms)
                    tokens.append(outcome.raw.usage.total)
        except TransientError as exc:
            raise HTTPException(status_code=502, detail=ErrorEnvelope(
                error_type="TransientError", message=str(exc), retryable=True,
                attempts=CHAT_MAX_RETRIES + 1).model_dump())
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=ErrorEnvelope(
                error_type="TimeoutError", message="provider timed out", retryable=True).model_dump())

        model = "mock-triage-1" if provider.is_mock else (
            settings.azure_openai_deployment if name == "azure" else settings.openai_model)
        residency = "EU/UK region" if name == "azure" else ("US default" if name == "openai" else "n/a (mock)")
        auth = getattr(provider, "auth_mode", "n/a")
        rows.append(summarize(name, latencies, tokens, model, settings,
                              residency=residency, auth=auth, simulated=provider.is_mock))

    return {"rows": [r.model_dump() for r in rows], "recommendation": recommend(rows)}
