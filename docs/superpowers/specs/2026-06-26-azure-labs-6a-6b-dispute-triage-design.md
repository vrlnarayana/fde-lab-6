# Azure AI Labs 6-A/6-B — Britannia Dispute-Triage Copilot (companion app) · Design

**Date:** 2026-06-26
**Author:** Lakshminarayanan (lead trainer) + Claude
**Programme:** FORGE FDE Academy · Batch-1 (Azure) · Day 06-Jul "Azure AI Foundry / IAM"
**Source kit:** `Azure_Trainee_Lab_Kit.md` (trainee-facing instructions, already written)
**Inspiration:** `../python-ai-scaffolding` (Lab 2-A — typed FastAPI + Streamlit scaffold)

## 1 · Purpose

Build the **runnable companion** the Azure Trainee Lab Kit refers to: a self-contained typed
service + Streamlit teaching app that lets learners (and the trainer rehearsing) work through
Labs **6-A, 6-B, Challenge 6-C, and Drill 6-D** and the Capstone, with **zero Azure access
required to learn** and a clean upgrade path to live Azure OpenAI.

The organising spine is the Week-1 scaffold's: **Type it · Validate it · Retry it · Time it out.**
The running case study is fixed: **Britannia Counties Bank — Dispute-Triage Copilot** (EU/UK
data residency · keyless · attributable to an identity).

### Non-goals (YAGNI)
- Not rebuilding the Week-1 scaffold — this is a sibling repo that mirrors its hexagon.
- Not provisioning real Azure for the learner — the app *proves* and *explains* the Azure steps;
  the trainee does the actual Foundry/RBAC/Bicep work on Azure per the kit.
- No private-endpoint / VNet networking in the app (noted as production-only in 6-C).
- No persistence/DB, no auth on the app itself, no multi-user state.

## 2 · Decisions (from brainstorming)

| Decision | Choice | Why |
|----------|--------|-----|
| App shape | **Companion + working copilot (both)** | Per-lab concept tabs PLUS the real capstone copilot tab. |
| Location | **New self-contained app** in `Azure-AI-Labs-6A-6B/` | Lab 2-A stays untouched as the "Week-1 scaffold" learners cloned; "point your scaffold at Azure" = a sibling repo. |
| Offline mode | **Offline-first, 3 auth modes** | Mock provider runs everything keyless; Azure key (6-A) + Azure keyless (6-B) light up live when configured. Honours the kit's "access is the #1 blocker" warning. |
| Client/server | **Keep Streamlit → HTTP → FastAPI split** | The boundary lab 2-A taught; the capstone's "a typed service" claim is literal. |
| Bicep | **Ship `infra/main.bicep` deploy-ready** | The 6-C artifact, reviewable by an auditor, baked with residency + keyless + least-priv RBAC. |

## 3 · Architecture

Mirrors lab 2-A's hexagon, specialised to the `DisputeTriage` domain.

```
Azure-AI-Labs-6A-6B/
  Azure_Trainee_Lab_Kit.md     trainee instructions (EXISTS — leave content, add a "run the app" pointer)
  README.md  00_START_HERE.md  app-level orientation (mirror lab 2-A tone)
  setup.sh  run.sh             venv+install+tests ; API:8000 + Streamlit:8501
  pyproject.toml  .python-version  .env.example
  api/
    config.py        Settings: azure key/endpoint/deployment, AUTH_MODE, direct-OpenAI key, published $ rates
    models.py        DisputeTriage + Urgency enum (kit's exact contract), TriageRequest/Response, BenchmarkResult
    errors.py        TransientError / ProviderError / ErrorEnvelope        (port of lab 2-A errors.py)
    client.py        resilient_triage(): timeout + bounded exponential backoff on TransientError
    triage.py        build_messages(dispute_text) + DisputeTriage.model_validate_json(...)  ("Validate it")
    benchmark.py     latency/cost harness: P50/P95, avg tokens, cost/1k, warm-up discard
    providers/
      base.py        TriageProvider Protocol  (port — frozen contract: name, is_mock, auth_mode, async triage())
      mock.py        deterministic DisputeTriage from keyword rules (offline-first; supports fail_first_k)
      azure_openai.py ONE adapter, two auth modes: api-key (6-A) | keyless DefaultAzureCredential (6-B)
      openai_direct.py direct OpenAI adapter (only used by the 6-D comparison drill)
      __init__.py    available_providers(), make_provider(), auth_posture()
    main.py          FastAPI: /health /providers /triage /benchmark /authcheck
  ui/streamlit_app.py  6 tabs (section 4)
  infra/main.bicep     Challenge 6-C IaC: residency param + disableLocalAuth + user-assigned identity + least-priv RBAC
  tests/               offline-green pytest (section 6)
```

### 3.1 · The port (frozen contract)

```python
class TriageProvider(Protocol):
    name: str
    is_mock: bool
    auth_mode: str   # "n/a" | "api-key" | "keyless"
    async def triage(self, request: TriageRequest) -> DisputeTriage: ...
```

Swapping providers/auth = swapping the adapter behind this port. The core (client, triage,
models) never changes — the hexagonal payoff the kit names in every "Week-1 scaffold link".

### 3.2 · The typed contract (from the kit's capstone, verbatim shape)

```python
class Urgency(str, Enum):
    low = "low"; medium = "medium"; high = "high"

class DisputeTriage(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    category: str            # card_fraud | duplicate_charge | subscription | atm | other
    urgency: Urgency
    needs_human_review: bool
    suggested_next_action: str
    pii_detected: bool
```

`TriageRequest`: `dispute_text: str`, `provider: str | None`, `fail_first_k: int` (mock retry lever).

## 4 · Streamlit tabs

Each tab renders the kit's marks as styled callouts: **banner** (indigo), **exercise** (amber),
**checkpoint** (green), **watch-out** (red), **Week-1 scaffold link** (lavender) — so the app and
the markdown kit read the same. Each tab pairs a LIVE demo with a "what's happening / why it
matters" hint, exactly like lab 2-A.

| # | Tab | Maps to | Live demo | Checkpoint surfaced |
|---|-----|---------|-----------|---------------------|
| 0 | Overview | §0 | Auth-posture board: active mode (mock / azure-key / azure-keyless), region, `disableLocalAuth` state; tools-ready checklist | App reachable; provider posture clear |
| 1 | 6-A Repoint | Lab 6-A | Paste dispute → typed `DisputeTriage`; "swap deployment by config only" (6-A.1); £89.99 sample (6-A.2) | Validated triage from EU/UK region, core unchanged |
| 2 | 6-B Keyless | Lab 6-B | Toggle key→identity; "keyless succeeds / key-based → `AuthenticationTypeDisabled`"; `listKeys` backdoor note (6-B.3) | Zero secrets · identity call · keys blocked |
| 3 | 6-C Challenge | Challenge | Render `infra/main.bicep`; run **contract tests** green against active adapter; force-429 → retry log (6-C.3) | az green · tests green · keyless · EU/UK |
| 4 | 6-D Benchmark | Drill | 20 prompts × {Azure, direct OpenAI}; P50/P95 / avg tokens / cost-per-1k table; warm-up discarded | Filled table + one-line recommendation |
| 5 | Capstone Copilot | Capstone | The real Dispute-Triage Copilot; the 6-row "demonstrate tomorrow" checklist as a live tracker | All six rows runnable |

## 5 · Offline-first behaviour (3 auth modes)

- **mock** (default): deterministic `DisputeTriage` from keyword rules → every tab + test runs with
  zero Azure. Supports `fail_first_k` to demo retry/backoff (the kit's 6-C.3 burst).
- **azure-key** (Lab 6-A): `AzureOpenAI(api_key=...)` — the temporary-key smoke test. Lights up when
  `AZURE_OPENAI_API_KEY` + endpoint are set.
- **azure-keyless** (Lab 6-B): `DefaultAzureCredential` + `get_bearer_token_provider`. Lights up when
  endpoint is set and `AUTH_MODE=keyless`.

When Azure is **not** configured: the 6-B keyless proof and the auth-posture board render the
*expected* state clearly labelled **"simulated"**, with the real `az` CLI proof shown alongside.
The 6-D benchmark runs **mock-vs-mock with injected synthetic latencies** offline so the harness and
table still render meaningfully (labelled as illustrative, not real measurements).

`auth_posture(settings)` returns `{mode, region, custom_subdomain, disable_local_auth, secrets_present, simulated}`
and powers the Overview board + 6-B proof + Capstone evidence line from one source of truth.

## 6 · Error handling & testing

**Errors** — same typed envelope as lab 2-A: `ProviderError`→HTTP 400, `TransientError`→502 (after
retries exhausted), `asyncio.TimeoutError`→504. A malformed model reply that fails
`DisputeTriage.model_validate_json` surfaces as a typed 422-style validation error in the triage
response (teaching moment: "downstream needs a strict shape, not free text").

**Tests (offline-green — the `setup.sh` gate):**
- `test_models.py` — strict rejects extra fields / type coercion; Urgency enum.
- `test_triage_mock.py` — mock returns a valid `DisputeTriage`; PII-bearing text flips `pii_detected`.
- `test_client_retries.py` — `fail_first_k` drives N retries then success; attempts counted; timeout raises.
- `test_benchmark.py` — P50/P95 math, warm-up discard, cost = tokens × rate.
- `test_providers.py` — factory: unknown name raises; unconfigured live provider raises; mock always available; `auth_posture` shapes.
- `test_api.py` — `/health /providers /triage /benchmark /authcheck` happy + error paths via FastAPI TestClient.
- `test_ui_smoke.py` — Streamlit app imports and renders without an API (graceful "start the API" path).

All pass with **no keys set**. House rule (from `fde-training/CLAUDE.md`): "works in `.venv`" is a
draft — final sign-off is a clean `./setup.sh` + `./run.sh` on the Techademy Azure VM.

## 7 · The Bicep artifact (`infra/main.bicep`)

Ship the kit's Challenge template deploy-ready: `location` param (residency), Azure OpenAI account
with `customSubDomainName` + `disableLocalAuth: true`, a `gpt-4o-mini` deployment, a user-assigned
managed identity, and a least-privilege `Cognitive Services OpenAI User` role assignment; outputs
`endpoint`, `deploymentName`, `appClientId`. `publicNetworkAccess` defaults to `Enabled` for laptop
labs with a comment that production Britannia is `Disabled` + private endpoint. The 6-C tab renders
this file and explains each hardening line.

## 8 · Out-of-scope / future
- Live private-endpoint networking; Azure Policy (Audit→Deny) tenant enforcement — explained, not built.
- Real cost numbers in 6-D when offline (synthetic, clearly labelled).
- CI wiring on the Azure VM (manual `setup.sh`/`run.sh` for now).

## 9 · Acceptance
- `./setup.sh` → all tests green with zero env vars.
- `./run.sh` → API:8000 + Streamlit:8501; all 6 tabs render and demo offline on mock.
- Setting the Azure trio + `AUTH_MODE` lights up azure-key / azure-keyless live without code edits.
- `infra/main.bicep` is valid and matches the kit.
- The kit markdown gains a "run the companion app" pointer; its lab content is unchanged.
