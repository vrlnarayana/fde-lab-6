# Azure AI Labs 6-A/6-B — Britannia Dispute-Triage Copilot · Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained, offline-first typed FastAPI + Streamlit companion app for Azure Labs 6-A/6-B/6-C/6-D that teaches "point your Week-1 scaffold at Azure" via a Britannia Dispute-Triage Copilot.

**Architecture:** Hexagonal port + adapters (mirrors `../python-ai-scaffolding`): a `TriageProvider` port behind which sit a deterministic `mock` adapter (offline), an Azure OpenAI adapter with two auth modes (api-key / keyless), and a direct-OpenAI adapter (benchmark only). A FastAPI wrapper exposes typed endpoints; a 6-tab Streamlit app is a pure HTTP client to it. Strict Pydantic validates every triage reply ("Validate it"); `resilient_triage` adds retries + timeout ("Retry it · Time it out").

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2 (strict), pydantic-settings, httpx, Streamlit, pytest (+ pytest-asyncio), openai + azure-identity (optional/lazy), Bicep (artifact only).

## Global Constraints

- Python `>=3.12`; run scripts via `./.venv/bin/python` (project venv).
- **Offline-first:** every non-optional test and the whole UI MUST work with **zero env vars / no keys**, on the `mock` provider. Live providers light up only when configured.
- Pydantic models use `ConfigDict(strict=True, extra="forbid")` for all request/response contracts.
- Typed error envelope only: `ProviderError`→HTTP 400, `TransientError`→HTTP 502 (retries exhausted), `asyncio.TimeoutError`→HTTP 504.
- The `DisputeTriage` contract is fixed (kit capstone): fields `category: str`, `urgency: Urgency{low,medium,high}`, `needs_human_review: bool`, `suggested_next_action: str`, `pii_detected: bool`.
- Live SDK imports (`openai`, `azure.identity`) are **lazy** (inside adapter `__init__`/methods) so startup is SDK-free.
- Running case study fixed: **Britannia Counties Bank**, EU/UK residency, keyless, identity-attributable.
- House rule: "works in `.venv`" is a draft; final sign-off is `./setup.sh` + `./run.sh` on the Azure VM.
- Package layout for setuptools: `["api", "api.providers", "ui"]`. All work happens in `Azure-AI-Labs-6A-6B/`.

---

### Task 1: Project scaffold + offline test harness

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.env.example`, `setup.sh`, `run.sh`, `.gitignore`
- Create: `api/__init__.py`, `api/providers/__init__.py` (empty placeholder, replaced in Task 5), `ui/__init__.py`
- Create: `tests/__init__.py`, `tests/conftest.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Produces: an installable package + a hermetic offline test env (`conftest.py` forces `DEFAULT_PROVIDER=mock` and blanks all keys before `api.config` imports).

- [ ] **Step 1: Write the failing test**

`tests/test_scaffold.py`:
```python
import os

def test_offline_env_is_hermetic():
    # conftest forces an offline, keyless environment regardless of any on-disk .env
    assert os.environ["DEFAULT_PROVIDER"] == "mock"
    assert os.environ["AZURE_OPENAI_API_KEY"] == ""
    assert os.environ["OPENAI_API_KEY"] == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_scaffold.py -q`
Expected: collection error / FAIL (no venv yet, or conftest missing).

- [ ] **Step 3: Create scaffold files**

`pyproject.toml`:
```toml
[project]
name = "azure-labs-6ab"
version = "0.1.0"
description = "Azure Labs 6-A/6-B — Britannia Dispute-Triage Copilot teaching app"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "uvicorn>=0.30",
    "pydantic>=2.7",
    "pydantic-settings>=2.2",
    "httpx>=0.27",
    "streamlit>=1.36",
]

[project.optional-dependencies]
dev = ["pytest>=8.2", "pytest-asyncio>=0.23"]
azure = ["openai>=1.30", "azure-identity>=1.17"]
openai = ["openai>=1.30"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["api", "api.providers", "ui"]
```

`.python-version`:
```
3.12
```

`.gitignore`:
```
.venv/
__pycache__/
*.egg-info/
.pytest_cache/
.env
.DS_Store
```

`.env.example`:
```
# Runs fully offline on the mock provider — no keys needed.
# --- Lab 6-A (temporary key) ---
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
# AZURE_REGION=westeurope
# --- Lab 6-B (keyless) ---  (omit AZURE_OPENAI_API_KEY; az login provides identity)
# AUTH_MODE=keyless                 # key | keyless
# AZURE_DISABLE_LOCAL_AUTH=true     # informational: reflects the resource setting
# --- Lab 6-D drill (direct OpenAI comparison) ---
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# --- App ---
# DEFAULT_PROVIDER=mock
# API_BASE_URL=http://localhost:8000
```

`tests/conftest.py`:
```python
"""Hermetic offline test env — set before api.config is imported.

pydantic-settings lets real env vars override .env; pytest imports conftest first,
so blanking keys + forcing mock here keeps the suite offline regardless of on-disk .env.
"""
import os

os.environ["DEFAULT_PROVIDER"] = "mock"
os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["AUTH_MODE"] = "key"
```

`setup.sh`:
```bash
#!/usr/bin/env bash
# Azure Labs 6-A/6-B — one-shot setup. Prefers uv; falls back to python3.12 venv.
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -e ".[dev]"
else
  python3.12 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip
  ./.venv/bin/python -m pip install -e ".[dev]"
fi

echo "Running tests..."
./.venv/bin/python -m pytest -q || test $? -eq 5
echo "Setup complete. Run ./run.sh to launch the API + Streamlit UI."
```

`run.sh`:
```bash
#!/usr/bin/env bash
# Azure Labs 6-A/6-B — launch the API (background) then the Streamlit UI (foreground).
set -euo pipefail
cd "$(dirname "$0")"

PY="./.venv/bin/python"
[ -x "$PY" ] || { echo "Run ./setup.sh first."; exit 1; }

API_PORT="${API_PORT:-8000}"
export API_BASE_URL="http://localhost:${API_PORT}"

echo "Starting API on ${API_BASE_URL} ..."
"$PY" -m uvicorn api.main:app --port "${API_PORT}" &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  if "$PY" -c "import httpx,sys; sys.exit(0 if httpx.get('${API_BASE_URL}/health').status_code==200 else 1)" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

echo "Starting Streamlit on http://localhost:8501 ..."
"$PY" -m streamlit run ui/streamlit_app.py
```

Create empty `api/__init__.py`, `api/providers/__init__.py`, `ui/__init__.py`, `tests/__init__.py`.

- [ ] **Step 4: Install + run the test**

Run: `chmod +x setup.sh run.sh && ./setup.sh && ./.venv/bin/python -m pytest tests/test_scaffold.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(6ab): project scaffold + hermetic offline test harness"
```

---

### Task 2: Typed domain models + error envelope

**Files:**
- Create: `api/errors.py`, `api/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces:
  - `errors.py`: `TransientError(Exception)`, `ProviderError(Exception)`, `ErrorEnvelope(BaseModel)` with `error_type:str, message:str, retryable:bool, attempts:int|None=None`.
  - `models.py`:
    - `Urgency(str, Enum)`: `low, medium, high`.
    - `DisputeTriage(BaseModel, strict)`: `category:str, urgency:Urgency, needs_human_review:bool, suggested_next_action:str, pii_detected:bool`.
    - `Usage(BaseModel, strict)`: `prompt_tokens:int=0, completion_tokens:int=0` with `total` property.
    - `ProviderTriageRaw(BaseModel, strict)`: `model:str, content:str, usage:Usage`.
    - `TriageRequest(BaseModel, strict)`: `dispute_text:str (min_length 1), provider:str|None=None, fail_first_k:int=0 (ge0 le10), force_bad_output:bool=False`.
    - `TriageResponse(BaseModel, strict)`: `provider:str, model:str, auth_mode:str, attempts:int, latency_ms:float, validated:bool, triage:DisputeTriage|None=None, error:str|None=None`.
    - `BenchmarkRequest(BaseModel, strict)`: `providers:list[str] (min_length 1), n:int=20 (ge2 le100), dispute_text:str (min_length 1)`.
    - `BenchmarkRow(BaseModel, strict)`: `provider:str, p50_ms:float, p95_ms:float, avg_tokens:float, cost_per_1k_calls:float, residency:str, auth:str, simulated:bool`.

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
import pytest
from pydantic import ValidationError
from api.models import (
    Urgency, DisputeTriage, TriageRequest, TriageResponse, BenchmarkRequest, Usage,
)

def test_dispute_triage_valid():
    t = DisputeTriage(category="card_fraud", urgency="high",
                      needs_human_review=True, suggested_next_action="Freeze card", pii_detected=True)
    assert t.urgency is Urgency.high

def test_dispute_triage_rejects_extra_field():
    with pytest.raises(ValidationError):
        DisputeTriage(category="other", urgency="low", needs_human_review=False,
                      suggested_next_action="x", pii_detected=False, confidence=0.9)

def test_dispute_triage_strict_no_coercion():
    with pytest.raises(ValidationError):
        DisputeTriage(category="other", urgency="low", needs_human_review="yes",  # str -> bool refused
                      suggested_next_action="x", pii_detected=False)

def test_triage_request_requires_nonempty_text():
    with pytest.raises(ValidationError):
        TriageRequest(dispute_text="")

def test_triage_request_fail_first_k_bounds():
    with pytest.raises(ValidationError):
        TriageRequest(dispute_text="hi", fail_first_k=99)

def test_usage_total():
    assert Usage(prompt_tokens=3, completion_tokens=4).total == 7

def test_benchmark_request_n_bounds():
    with pytest.raises(ValidationError):
        BenchmarkRequest(providers=["mock"], n=1, dispute_text="x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_models.py -q`
Expected: FAIL (`ModuleNotFoundError: api.models`).

- [ ] **Step 3: Write the implementation**

`api/errors.py`:
```python
from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class ErrorEnvelope(BaseModel):
    """The single typed shape every failure is surfaced as."""
    model_config = ConfigDict(extra="forbid")
    error_type: str
    message: str
    retryable: bool
    attempts: int | None = None


class TransientError(Exception):
    """Retryable provider error (429 / 5xx). The client backs off and retries."""


class ProviderError(Exception):
    """Non-retryable provider error (bad request / auth). The client gives up."""
```

`api/models.py`:
```python
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

STRICT = ConfigDict(strict=True, extra="forbid")


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DisputeTriage(BaseModel):
    """The typed contract the copilot must return (kit capstone shape)."""
    model_config = STRICT
    category: str = Field(description="card_fraud | duplicate_charge | subscription | atm | other")
    urgency: Urgency
    needs_human_review: bool
    suggested_next_action: str
    pii_detected: bool = Field(description="true if text holds PII to redact before logging")


class Usage(BaseModel):
    model_config = STRICT
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class ProviderTriageRaw(BaseModel):
    """A provider's raw reply — content is JSON to be validated downstream ('Validate it')."""
    model_config = STRICT
    model: str
    content: str
    usage: Usage


class TriageRequest(BaseModel):
    model_config = STRICT
    dispute_text: str = Field(min_length=1)
    provider: str | None = None
    fail_first_k: int = Field(default=0, ge=0, le=10)        # mock retry lever
    force_bad_output: bool = False                            # mock malformed-output lever


class TriageResponse(BaseModel):
    model_config = STRICT
    provider: str
    model: str
    auth_mode: str
    attempts: int
    latency_ms: float
    validated: bool
    triage: DisputeTriage | None = None
    error: str | None = None


class BenchmarkRequest(BaseModel):
    model_config = STRICT
    providers: list[str] = Field(min_length=1)
    n: int = Field(default=20, ge=2, le=100)
    dispute_text: str = Field(min_length=1)


class BenchmarkRow(BaseModel):
    model_config = STRICT
    provider: str
    p50_ms: float
    p95_ms: float
    avg_tokens: float
    cost_per_1k_calls: float
    residency: str
    auth: str
    simulated: bool
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_models.py -q`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add api/errors.py api/models.py tests/test_models.py
git commit -m "feat(6ab): DisputeTriage domain models + typed error envelope"
```

---

### Task 3: Triage parser ("Validate it")

**Files:**
- Create: `api/triage.py`
- Test: `tests/test_triage_parse.py`

**Interfaces:**
- Consumes: `DisputeTriage` (Task 2).
- Produces:
  - `SYSTEM_PROMPT: str` — instructs a model to return strict JSON for `DisputeTriage`.
  - `build_messages(dispute_text: str) -> list[dict]` — `[{role:system,...},{role:user,...}]`.
  - `parse_triage(raw_json: str) -> tuple[DisputeTriage | None, str | None]` — `(triage, error)`, never raises.

- [ ] **Step 1: Write the failing test**

`tests/test_triage_parse.py`:
```python
from api.triage import parse_triage, build_messages

VALID = ('{"category":"card_fraud","urgency":"high","needs_human_review":true,'
         '"suggested_next_action":"Freeze the card","pii_detected":true}')

def test_parse_valid():
    triage, err = parse_triage(VALID)
    assert err is None
    assert triage.category == "card_fraud"

def test_parse_not_json():
    triage, err = parse_triage("{not json")
    assert triage is None
    assert "JSON" in err

def test_parse_schema_violation():
    triage, err = parse_triage('{"category":"x","urgency":"SUPER","needs_human_review":true,'
                               '"suggested_next_action":"y","pii_detected":false}')
    assert triage is None
    assert "validation" in err.lower()

def test_build_messages_shape():
    msgs = build_messages("I was charged twice")
    assert msgs[0]["role"] == "system"
    assert msgs[-1]["role"] == "user"
    assert "charged twice" in msgs[-1]["content"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_triage_parse.py -q`
Expected: FAIL (`ModuleNotFoundError: api.triage`).

- [ ] **Step 3: Write the implementation**

`api/triage.py`:
```python
from __future__ import annotations
import json
from pydantic import ValidationError
from api.models import DisputeTriage

SYSTEM_PROMPT = (
    "You are a UK retail bank's dispute-triage assistant. Read the customer's free-text "
    "dispute and return ONLY a JSON object with exactly these keys: "
    "category (one of: card_fraud, duplicate_charge, subscription, atm, other), "
    "urgency (one of: low, medium, high), needs_human_review (boolean), "
    "suggested_next_action (string), pii_detected (boolean — true if the text contains PII "
    "to redact before logging). No prose, no markdown — JSON only."
)


def build_messages(dispute_text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": dispute_text},
    ]


def parse_triage(raw_json: str) -> tuple[DisputeTriage | None, str | None]:
    """Validate a raw model reply into a DisputeTriage. Never raises."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return None, f"reply is not valid JSON: {exc}"
    try:
        return DisputeTriage.model_validate(data), None
    except ValidationError as exc:
        return None, f"reply failed validation: {exc.errors(include_url=False)}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_triage_parse.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add api/triage.py tests/test_triage_parse.py
git commit -m "feat(6ab): triage prompt builder + strict reply parser"
```

---

### Task 4: Port + Mock provider (the offline teaching engine)

**Files:**
- Create: `api/providers/base.py`, `api/providers/mock.py`
- Test: `tests/test_mock_provider.py`

**Interfaces:**
- Consumes: `TriageRequest`, `ProviderTriageRaw`, `Usage` (Task 2); `TransientError` (Task 2).
- Produces:
  - `base.py`: `TriageProvider(Protocol)` with attrs `name:str, is_mock:bool, auth_mode:str` and `async def triage(self, request: TriageRequest) -> ProviderTriageRaw`.
  - `mock.py`: `MockProvider(fail_first_k:int=0, force_bad_output:bool=False)` with `name="mock", is_mock=True, auth_mode="n/a"`; deterministic keyword-rule triage; raises `TransientError` on first `k` calls; emits malformed JSON when `force_bad_output`.

- [ ] **Step 1: Write the failing test**

`tests/test_mock_provider.py`:
```python
import json
import pytest
from api.models import TriageRequest
from api.errors import TransientError
from api.providers.mock import MockProvider
from api.triage import parse_triage

async def test_mock_returns_valid_triage():
    raw = await MockProvider().triage(TriageRequest(dispute_text="I never authorised this charge"))
    triage, err = parse_triage(raw.content)
    assert err is None
    assert triage.category == "card_fraud"
    assert triage.needs_human_review is True

async def test_mock_detects_pii_from_digits():
    raw = await MockProvider().triage(TriageRequest(dispute_text="charged £89.99 on 3 June"))
    triage, _ = parse_triage(raw.content)
    assert triage.pii_detected is True

async def test_mock_no_pii_for_plain_text():
    raw = await MockProvider().triage(TriageRequest(dispute_text="my subscription renewed"))
    triage, _ = parse_triage(raw.content)
    assert triage.pii_detected is False
    assert triage.category == "subscription"

async def test_mock_fail_first_k_then_success():
    p = MockProvider(fail_first_k=2)
    req = TriageRequest(dispute_text="hi")
    for _ in range(2):
        with pytest.raises(TransientError):
            await p.triage(req)
    raw = await p.triage(req)
    assert raw.model == "mock-triage-1"

async def test_mock_force_bad_output_is_unparseable():
    raw = await MockProvider(force_bad_output=True).triage(TriageRequest(dispute_text="x"))
    triage, err = parse_triage(raw.content)
    assert triage is None and err is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_mock_provider.py -q`
Expected: FAIL (`ModuleNotFoundError: api.providers.mock`).

- [ ] **Step 3: Write the implementation**

`api/providers/base.py`:
```python
from __future__ import annotations
from typing import Protocol
from api.models import TriageRequest, ProviderTriageRaw


class TriageProvider(Protocol):
    """The contract every adapter satisfies. Structural typing — no inheritance."""
    name: str
    is_mock: bool
    auth_mode: str   # "n/a" | "api-key" | "keyless"

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw: ...
```

`api/providers/mock.py`:
```python
from __future__ import annotations
import json
from api.errors import TransientError
from api.models import TriageRequest, ProviderTriageRaw, Usage


def _classify(text: str) -> dict:
    t = text.lower()
    pii = any(ch.isdigit() for ch in text) or "£" in text
    if any(k in t for k in ("never authorised", "didn't authorise", "did not authorise",
                            "unauthor", "fraud", "don't recognise", "do not recognise")):
        category, urgency, action = "card_fraud", "high", "Freeze the card and open a fraud case."
    elif any(k in t for k in ("twice", "duplicate", "two times", "double charged")):
        category, urgency, action = "duplicate_charge", "medium", "Check for a duplicate authorisation and refund if confirmed."
    elif any(k in t for k in ("subscription", "renew", "recurring")):
        category, urgency, action = "subscription", "low", "Locate the recurring mandate and offer cancellation."
    elif any(k in t for k in ("atm", "cash machine", "withdraw")):
        category, urgency, action = "atm", "medium", "Pull ATM journal for the terminal and timestamp."
    else:
        category, urgency, action = "other", "low", "Route to general disputes queue for review."
    needs_human = urgency == "high" or pii
    return {
        "category": category,
        "urgency": urgency,
        "needs_human_review": needs_human,
        "suggested_next_action": action,
        "pii_detected": pii,
    }


class MockProvider:
    """Deterministic, offline triage — the teaching engine.

    fail_first_k:    raise TransientError on the first k calls (retry/backoff demo).
    force_bad_output: emit malformed JSON (the 'Validate it' failure demo).
    """
    name = "mock"
    is_mock = True
    auth_mode = "n/a"

    def __init__(self, fail_first_k: int = 0, force_bad_output: bool = False):
        self._fails_left = fail_first_k
        self.force_bad_output = force_bad_output

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw:
        if self._fails_left > 0:
            self._fails_left -= 1
            raise TransientError("429 rate limited (mock)")
        text = request.dispute_text
        content = "{not valid json" if self.force_bad_output else json.dumps(_classify(text))
        return ProviderTriageRaw(
            model="mock-triage-1",
            content=content,
            usage=Usage(prompt_tokens=len(text.split()), completion_tokens=12),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_mock_provider.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add api/providers/base.py api/providers/mock.py tests/test_mock_provider.py
git commit -m "feat(6ab): TriageProvider port + deterministic mock provider"
```

---

### Task 5: Config + provider factory + auth posture

**Files:**
- Create: `api/config.py`, `api/providers/azure_openai.py`, `api/providers/openai_direct.py`
- Modify: `api/providers/__init__.py` (replace placeholder)
- Test: `tests/test_providers.py`

**Interfaces:**
- Consumes: `Settings`, `MockProvider`, `ProviderError`, `TriageProvider`.
- Produces:
  - `config.py`: `Settings(BaseSettings)` fields: `azure_openai_api_key:str|None`, `azure_openai_endpoint:str|None`, `azure_openai_deployment:str="gpt-4o-mini"`, `azure_region:str="westeurope"`, `auth_mode:str="key"`, `azure_disable_local_auth:bool=False`, `openai_api_key:str|None`, `openai_model:str="gpt-4o-mini"`, `default_provider:str="mock"`, `rate_per_1k_tokens:dict[str,float]={"gpt-4o-mini":0.0006,"gpt-4o":0.0075,"mock-triage-1":0.0}`. Module-level `settings = Settings()`.
  - `providers/__init__.py`:
    - `available_providers(settings) -> list[dict]` rows `{name, available, is_mock, auth_mode}` for mock/azure/openai.
    - `make_provider(name, settings, *, fail_first_k=0, force_bad_output=False) -> TriageProvider`.
    - `auth_posture(settings) -> dict` `{mode, region, custom_subdomain, disable_local_auth, secrets_present, simulated}`.
  - `azure_openai.py`: `AzureOpenAIProvider(settings)` — `name="azure", is_mock=False, auth_mode = settings.auth_mode` ("api-key"/"keyless"); raises `ProviderError` if endpoint unset; lazy-imports `openai` (+ `azure.identity` when keyless).
  - `openai_direct.py`: `OpenAIDirectProvider(settings)` — `name="openai", is_mock=False, auth_mode="api-key"`; raises `ProviderError` if key unset; lazy-imports `openai`.

- [ ] **Step 1: Write the failing test**

`tests/test_providers.py`:
```python
import pytest
from api.config import Settings
from api.errors import ProviderError
from api.providers import available_providers, make_provider, auth_posture
from api.providers.mock import MockProvider

def offline_settings(**kw):
    base = dict(azure_openai_api_key=None, azure_openai_endpoint=None,
                openai_api_key=None, default_provider="mock", auth_mode="key")
    base.update(kw)
    return Settings(**base)

def test_mock_always_available():
    rows = {r["name"]: r for r in available_providers(offline_settings())}
    assert rows["mock"]["available"] is True
    assert rows["azure"]["available"] is False
    assert rows["openai"]["available"] is False

def test_make_provider_defaults_to_mock():
    p = make_provider(None, offline_settings())
    assert isinstance(p, MockProvider)

def test_make_provider_unknown_raises():
    with pytest.raises(ProviderError):
        make_provider("gemini", offline_settings())

def test_make_provider_unconfigured_azure_raises():
    with pytest.raises(ProviderError):
        make_provider("azure", offline_settings())

def test_force_bad_output_routes_through_mock():
    p = make_provider("azure", offline_settings(), force_bad_output=True)
    assert isinstance(p, MockProvider) and p.force_bad_output is True

def test_auth_posture_offline_is_simulated():
    post = auth_posture(offline_settings())
    assert post["simulated"] is True
    assert post["secrets_present"] is False
    assert post["region"] == "westeurope"

def test_auth_posture_azure_key_configured():
    s = offline_settings(azure_openai_api_key="k", azure_openai_endpoint="https://x.openai.azure.com", auth_mode="key")
    post = auth_posture(s)
    assert post["simulated"] is False
    assert post["mode"] == "api-key"
    assert post["secrets_present"] is True

def test_auth_posture_keyless_no_secret():
    s = offline_settings(azure_openai_endpoint="https://x.openai.azure.com", auth_mode="keyless")
    post = auth_posture(s)
    assert post["mode"] == "keyless"
    assert post["secrets_present"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_providers.py -q`
Expected: FAIL (`ModuleNotFoundError: api.config`).

- [ ] **Step 3: Write the implementation**

`api/config.py`:
```python
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_region: str = "westeurope"
    auth_mode: str = "key"                 # key | keyless
    azure_disable_local_auth: bool = False

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    default_provider: str = "mock"

    # Published blended $/1K tokens (indicative — see 6-D watch-out; verify before quoting).
    rate_per_1k_tokens: dict[str, float] = {
        "gpt-4o-mini": 0.0006,
        "gpt-4o": 0.0075,
        "mock-triage-1": 0.0,
    }


settings = Settings()
```

`api/providers/azure_openai.py`:
```python
from __future__ import annotations
from api.config import Settings
from api.errors import ProviderError
from api.models import TriageRequest, ProviderTriageRaw, Usage
from api.triage import build_messages


class AzureOpenAIProvider:
    """Lab 6-A (api-key) and 6-B (keyless) — only the auth path differs."""
    name = "azure"
    is_mock = False

    def __init__(self, settings: Settings):
        if not settings.azure_openai_endpoint:
            raise ProviderError("AZURE_OPENAI_ENDPOINT not set")
        self.auth_mode = "keyless" if settings.auth_mode == "keyless" else "api-key"
        self._deployment = settings.azure_openai_deployment
        from openai import AsyncAzureOpenAI  # lazy

        if self.auth_mode == "keyless":
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider  # lazy
            token = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_ad_token_provider=token,        # identity, not a secret
                api_version="2024-10-21",
            )
        else:
            if not settings.azure_openai_api_key:
                raise ProviderError("AZURE_OPENAI_API_KEY not set (auth_mode=key)")
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,  # REMOVED in Lab 6-B
                api_version="2024-10-21",
            )

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw:
        resp = await self._client.chat.completions.create(
            model=self._deployment,
            messages=build_messages(request.dispute_text),
            response_format={"type": "json_object"},
            timeout=10,
        )
        usage = resp.usage
        return ProviderTriageRaw(
            model=resp.model,
            content=resp.choices[0].message.content or "",
            usage=Usage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            ),
        )
```

`api/providers/openai_direct.py`:
```python
from __future__ import annotations
from api.config import Settings
from api.errors import ProviderError
from api.models import TriageRequest, ProviderTriageRaw, Usage
from api.triage import build_messages


class OpenAIDirectProvider:
    """Direct OpenAI — used only by the 6-D latency/cost drill (US default, API key)."""
    name = "openai"
    is_mock = False
    auth_mode = "api-key"

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY not set")
        from openai import AsyncOpenAI  # lazy
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=build_messages(request.dispute_text),
            response_format={"type": "json_object"},
            timeout=10,
        )
        usage = resp.usage
        return ProviderTriageRaw(
            model=resp.model,
            content=resp.choices[0].message.content or "",
            usage=Usage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            ),
        )
```

`api/providers/__init__.py` (replace placeholder):
```python
from __future__ import annotations
from api.config import Settings
from api.errors import ProviderError
from api.providers.base import TriageProvider
from api.providers.mock import MockProvider


def _azure_ready(s: Settings) -> bool:
    if not s.azure_openai_endpoint:
        return False
    return s.auth_mode == "keyless" or bool(s.azure_openai_api_key)


def _availability(s: Settings) -> dict[str, bool]:
    return {"azure": _azure_ready(s), "openai": bool(s.openai_api_key)}


def available_providers(s: Settings) -> list[dict]:
    avail = _availability(s)
    rows = [{"name": "mock", "available": True, "is_mock": True, "auth_mode": "n/a"}]
    rows.append({"name": "azure", "available": avail["azure"], "is_mock": False,
                 "auth_mode": "keyless" if s.auth_mode == "keyless" else "api-key"})
    rows.append({"name": "openai", "available": avail["openai"], "is_mock": False, "auth_mode": "api-key"})
    return rows


def auth_posture(s: Settings) -> dict:
    azure_ready = _azure_ready(s)
    return {
        "mode": ("keyless" if s.auth_mode == "keyless" else "api-key") if azure_ready else "mock",
        "region": s.azure_region,
        "custom_subdomain": bool(s.azure_openai_endpoint and ".openai.azure.com" in s.azure_openai_endpoint),
        "disable_local_auth": s.azure_disable_local_auth,
        "secrets_present": bool(s.azure_openai_api_key or s.openai_api_key),
        "simulated": not azure_ready,
    }


def make_provider(name, s: Settings, *, fail_first_k: int = 0, force_bad_output: bool = False) -> TriageProvider:
    # Malformed-output is a deterministic teaching sim — always route through the mock.
    if name in (None, "mock") or force_bad_output:
        return MockProvider(fail_first_k=fail_first_k, force_bad_output=force_bad_output)

    avail = _availability(s)
    if name not in avail:
        raise ProviderError(f"unknown provider: {name}")
    if not avail[name]:
        raise ProviderError(f"provider '{name}' is not configured")

    if name == "azure":
        from api.providers.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider(s)
    if name == "openai":
        from api.providers.openai_direct import OpenAIDirectProvider
        return OpenAIDirectProvider(s)
    raise ProviderError(f"unknown provider: {name}")  # unreachable
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_providers.py -q`
Expected: PASS (8 passed).

- [ ] **Step 5: Commit**

```bash
git add api/config.py api/providers/ tests/test_providers.py
git commit -m "feat(6ab): settings, Azure/OpenAI adapters, factory + auth posture"
```

---

### Task 6: Resilient triage client (retry + timeout)

**Files:**
- Create: `api/client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: `TriageProvider`, `TriageRequest`, `ProviderTriageRaw`, `TransientError`.
- Produces:
  - `CallOutcome(BaseModel, strict)`: `raw: ProviderTriageRaw, attempts: int, latency_ms: float`.
  - `async def resilient_triage(provider, request, *, max_retries=3, base_delay=0.01, timeout=10.0) -> CallOutcome` — times the call, backs off on `TransientError`, re-raises after exhaustion; `asyncio.TimeoutError` propagates.

- [ ] **Step 1: Write the failing test**

`tests/test_client.py`:
```python
import asyncio
import pytest
from api.client import resilient_triage, CallOutcome
from api.models import TriageRequest
from api.errors import TransientError
from api.providers.mock import MockProvider

REQ = TriageRequest(dispute_text="I never authorised this")

async def test_succeeds_first_try():
    out = await resilient_triage(MockProvider(), REQ, base_delay=0.001)
    assert isinstance(out, CallOutcome)
    assert out.attempts == 1
    assert out.latency_ms >= 0.0

async def test_retries_then_succeeds():
    out = await resilient_triage(MockProvider(fail_first_k=2), REQ, base_delay=0.001)
    assert out.attempts == 3

async def test_raises_after_retries_exhausted():
    with pytest.raises(TransientError):
        await resilient_triage(MockProvider(fail_first_k=9), REQ, max_retries=2, base_delay=0.001)

async def test_timeout_propagates():
    class Slow(MockProvider):
        async def triage(self, request):
            await asyncio.sleep(0.2)
            return await super().triage(request)
    with pytest.raises(asyncio.TimeoutError):
        await resilient_triage(Slow(), REQ, timeout=0.01)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_client.py -q`
Expected: FAIL (`ModuleNotFoundError: api.client`).

- [ ] **Step 3: Write the implementation**

`api/client.py`:
```python
from __future__ import annotations
import asyncio
import time
from pydantic import BaseModel, ConfigDict
from api.errors import TransientError
from api.models import TriageRequest, ProviderTriageRaw
from api.providers.base import TriageProvider


class CallOutcome(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", arbitrary_types_allowed=True)
    raw: ProviderTriageRaw
    attempts: int
    latency_ms: float


async def resilient_triage(
    provider: TriageProvider,
    request: TriageRequest,
    *,
    max_retries: int = 3,
    base_delay: float = 0.01,
    timeout: float = 10.0,
) -> CallOutcome:
    """Call a provider with a timeout and bounded exponential backoff on TransientError.

    Returns a CallOutcome stamped with attempts + wall-clock latency. Re-raises
    TransientError once retries are exhausted; asyncio.TimeoutError propagates.
    """
    attempt = 0
    start = time.perf_counter()
    while True:
        attempt += 1
        try:
            raw = await asyncio.wait_for(provider.triage(request), timeout=timeout)
        except TransientError:
            if attempt > max_retries:
                raise
            await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
            continue
        latency_ms = (time.perf_counter() - start) * 1000.0
        return CallOutcome(raw=raw, attempts=attempt, latency_ms=latency_ms)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_client.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add api/client.py tests/test_client.py
git commit -m "feat(6ab): resilient_triage client with retry + timeout"
```

---

### Task 7: Benchmark harness (6-D math)

**Files:**
- Create: `api/benchmark.py`
- Test: `tests/test_benchmark.py`

**Interfaces:**
- Consumes: `BenchmarkRow` (Task 2), `Settings` (Task 5).
- Produces:
  - `percentile(sorted_vals: list[float], p: float) -> float` — linear-interpolation percentile.
  - `summarize(provider:str, latencies_ms:list[float], token_counts:list[int], model:str, settings, *, residency:str, auth:str, simulated:bool) -> BenchmarkRow` — discards the warm-up (first) sample, computes p50/p95, avg tokens, `cost_per_1k_calls = avg_tokens * rate_per_1k_tokens[model]`.
  - `synthetic_latencies(n:int, base_ms:float, step_ms:float) -> list[float]` — deterministic illustrative latencies for offline mock-vs-mock.
  - `recommend(rows: list[BenchmarkRow]) -> str` — one-line Britannia recommendation (residency/identity win).

- [ ] **Step 1: Write the failing test**

`tests/test_benchmark.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_benchmark.py -q`
Expected: FAIL (`ModuleNotFoundError: api.benchmark`).

- [ ] **Step 3: Write the implementation**

`api/benchmark.py`:
```python
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
    azure = next((r for r in rows if r.provider == "azure"), None)
    if azure is not None:
        return ("For Britannia, choose Azure OpenAI: the EU/UK residency + keyless identity "
                "envelope is the deciding constraint, and it wins even at latency/price parity.")
    return "Insufficient data — run the Azure row to make the residency/identity call."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_benchmark.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add api/benchmark.py tests/test_benchmark.py
git commit -m "feat(6ab): latency/cost benchmark harness (6-D math)"
```

---

### Task 8: FastAPI wrapper (endpoints)

**Files:**
- Create: `api/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: everything above.
- Produces FastAPI `app` with:
  - `GET /health` → `{"status":"ok"}`.
  - `GET /providers` → `{"providers":[...], "default":..., "posture":{...}}`.
  - `GET /authcheck` → `auth_posture(settings)` + `{"checklist": {...}}`.
  - `POST /triage` (`TriageRequest`) → `TriageResponse` (validates the raw reply; `validated`/`error` set accordingly). Errors: `ProviderError`→400, `TransientError`→502, timeout→504.
  - `POST /benchmark` (`BenchmarkRequest`) → `{"rows":[BenchmarkRow...], "recommendation": str}`. Mock provider rows use `synthetic_latencies` and are flagged `simulated=True`.

- [ ] **Step 1: Write the failing test**

`tests/test_api.py`:
```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_providers_lists_mock_default_and_posture():
    data = client.get("/providers").json()
    names = {p["name"] for p in data["providers"]}
    assert {"mock", "azure", "openai"} <= names
    assert data["default"] == "mock"
    assert data["posture"]["simulated"] is True

def test_triage_happy_path_validated():
    r = client.post("/triage", json={"dispute_text": "I never authorised this £50 charge"})
    assert r.status_code == 200
    body = r.json()
    assert body["validated"] is True
    assert body["triage"]["category"] == "card_fraud"
    assert body["attempts"] == 1
    assert body["auth_mode"] == "n/a"

def test_triage_retry_demo_counts_attempts():
    r = client.post("/triage", json={"dispute_text": "hi", "fail_first_k": 2})
    assert r.status_code == 200
    assert r.json()["attempts"] == 3

def test_triage_malformed_output_is_unvalidated_not_500():
    r = client.post("/triage", json={"dispute_text": "x", "force_bad_output": True})
    assert r.status_code == 200
    body = r.json()
    assert body["validated"] is False
    assert body["triage"] is None
    assert body["error"]

def test_triage_unknown_provider_400():
    r = client.post("/triage", json={"dispute_text": "x", "provider": "gemini"})
    assert r.status_code == 400
    assert r.json()["detail"]["error_type"] == "ProviderError"

def test_triage_strict_rejects_extra_field_422():
    r = client.post("/triage", json={"dispute_text": "x", "temperature": 0.7})
    assert r.status_code == 422

def test_benchmark_mock_rows_simulated():
    r = client.post("/benchmark", json={"providers": ["mock"], "n": 6, "dispute_text": "twice charged"})
    assert r.status_code == 200
    data = r.json()
    assert data["rows"][0]["simulated"] is True
    assert "recommendation" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_api.py -q`
Expected: FAIL (`ModuleNotFoundError: api.main`).

- [ ] **Step 3: Write the implementation**

`api/main.py`:
```python
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

        model = "mock-triage-1" if provider.is_mock else (
            settings.azure_openai_deployment if name == "azure" else settings.openai_model)
        residency = "EU/UK region" if name == "azure" else ("US default" if name == "openai" else "n/a (mock)")
        auth = getattr(provider, "auth_mode", "n/a")
        rows.append(summarize(name, latencies, tokens, model, settings,
                              residency=residency, auth=auth, simulated=provider.is_mock))

    return {"rows": [r.model_dump() for r in rows], "recommendation": recommend(rows)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_api.py -q`
Expected: PASS (8 passed).

- [ ] **Step 5: Commit**

```bash
git add api/main.py tests/test_api.py
git commit -m "feat(6ab): FastAPI wrapper — triage, benchmark, authcheck endpoints"
```

---

### Task 9: Streamlit teaching app (6 tabs)

**Files:**
- Create: `ui/streamlit_app.py`
- Test: `tests/test_ui_smoke.py`

**Interfaces:**
- Consumes: the running API over HTTP (`API_BASE_URL`, default `http://localhost:8000`).
- Produces: a 6-tab Streamlit app. Module-level helpers must import without a running API (smoke test imports the module and calls the callout helpers).

- [ ] **Step 1: Write the failing test**

`tests/test_ui_smoke.py`:
```python
import importlib

def test_ui_module_imports():
    mod = importlib.import_module("ui.streamlit_app")
    assert hasattr(mod, "api_url")
    assert mod.api_url("/health").endswith("/health")

def test_callout_helpers_exist():
    mod = importlib.import_module("ui.streamlit_app")
    for fn in ("banner", "exercise", "checkpoint", "watchout", "scaffold_link", "hint"):
        assert callable(getattr(mod, fn))

def test_tab_renderers_exist():
    mod = importlib.import_module("ui.streamlit_app")
    for fn in ("tab_overview", "tab_6a", "tab_6b", "tab_6c", "tab_6d", "tab_capstone"):
        assert callable(getattr(mod, fn))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_ui_smoke.py -q`
Expected: FAIL (`ModuleNotFoundError: ui.streamlit_app`).

- [ ] **Step 3: Write the implementation**

`ui/streamlit_app.py`:
```python
# ui/streamlit_app.py
"""Azure Labs 6-A/6-B — Britannia Dispute-Triage Copilot teaching app.

Six tabs, one per lab. Each pairs a LIVE demo with the kit's marks
(banner / exercise / checkpoint / watch-out / Week-1 scaffold link).
A pure HTTP client to the FastAPI wrapper — it never imports the SDKs.
Run the API first (./run.sh does both).
"""
from __future__ import annotations
import json
import os
import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SAMPLE = "I was charged £89.99 by 'GLOBL-SVC' twice on 3 June, I never authorised it."


def api_url(path: str) -> str:
    return f"{API_BASE_URL.rstrip('/')}{path}"


def _get(path: str):
    return httpx.get(api_url(path), timeout=30.0)


def _post(path: str, payload: dict):
    return httpx.post(api_url(path), json=payload, timeout=60.0)


# ---- kit-style callouts --------------------------------------------------

def banner(title: str, body: str) -> None:
    st.markdown(
        f"<div style='background:#3730a3;color:#fff;padding:12px 16px;border-radius:8px'>"
        f"<b>{title}</b><br>{body}</div>", unsafe_allow_html=True)
    st.write("")

def exercise(title: str, body: str) -> None:
    st.markdown(
        f"<div style='background:#fef3c7;border-left:5px solid #f59e0b;padding:10px 14px;border-radius:6px'>"
        f"⬛ <b>{title}</b><br>{body}</div>", unsafe_allow_html=True)
    st.write("")

def checkpoint(body: str) -> None:
    st.markdown(
        f"<div style='background:#dcfce7;border-left:5px solid #16a34a;padding:10px 14px;border-radius:6px'>"
        f"✅ <b>Checkpoint:</b> {body}</div>", unsafe_allow_html=True)
    st.write("")

def watchout(body: str) -> None:
    st.markdown(
        f"<div style='background:#fee2e2;border-left:5px solid #dc2626;padding:10px 14px;border-radius:6px'>"
        f"⚠️ <b>Watch out:</b> {body}</div>", unsafe_allow_html=True)
    st.write("")

def scaffold_link(body: str) -> None:
    st.markdown(
        f"<div style='background:#ede9fe;border-left:5px solid #7c3aed;padding:10px 14px;border-radius:6px'>"
        f"↩ <b>Week-1 scaffold link:</b> {body}</div>", unsafe_allow_html=True)
    st.write("")

def hint(title: str, body: str) -> None:
    with st.expander(f"💡 {title}"):
        st.markdown(body)


def _api_down(exc) -> None:
    st.error(f"Cannot reach the API at {API_BASE_URL}. Start it with ./run.sh. ({exc})")


def _render_triage(dispute_text: str, *, fail_first_k: int = 0, force_bad_output: bool = False,
                   provider: str | None = None) -> None:
    payload = {"dispute_text": dispute_text, "fail_first_k": fail_first_k,
               "force_bad_output": force_bad_output}
    if provider:
        payload["provider"] = provider
    try:
        resp = _post("/triage", payload)
    except Exception as exc:
        _api_down(exc); return
    body = resp.json()
    if resp.status_code != 200:
        st.error(f"HTTP {resp.status_code}"); st.json(body); return
    cols = st.columns(3)
    cols[0].metric("Provider", body["provider"])
    cols[1].metric("Auth mode", body["auth_mode"])
    cols[2].metric("Attempts", body["attempts"])
    if body["validated"]:
        st.success(f"Validated DisputeTriage in {body['latency_ms']} ms ✅")
        st.json(body["triage"])
    else:
        st.error("Reply failed strict validation — this is 'Validate it' catching drift:")
        st.code(body["error"])


# ---- tabs ----------------------------------------------------------------

def tab_overview() -> None:
    banner("§0 · Britannia Counties Bank — Dispute-Triage Copilot",
            "EU/UK residency · keyless · attributable to an identity. "
            "This app is your Week-1 scaffold pointed at Azure.")
    st.subheader("Auth posture")
    try:
        data = _get("/providers").json()
    except Exception as exc:
        _api_down(exc); return
    post = data["posture"]
    cols = st.columns(4)
    cols[0].metric("Active mode", post["mode"])
    cols[1].metric("Region", post["region"])
    cols[2].metric("Local auth", "disabled" if post["disable_local_auth"] else "enabled")
    cols[3].metric("Secrets in use", "yes" if post["secrets_present"] else "no")
    if post["simulated"]:
        st.info("No Azure configured — keyless/identity proofs render as **simulated**. "
                "Set the Azure trio + AUTH_MODE in `.env` to go live.")
    st.subheader("Providers")
    st.table([{k: p[k] for k in ("name", "available", "auth_mode")} for p in data["providers"]])
    hint("Why a client/server split?",
         "This Streamlit UI makes **HTTP calls** to a typed FastAPI wrapper (`api/main.py`); it never "
         "touches the OpenAI/Azure SDKs. That boundary is what an FDE ships — a typed service others call.")


def tab_6a() -> None:
    banner("LAB 6-A · Deploy a model · invoke from your scaffold",
            "Stand up an Azure OpenAI deployment in your residency region and call it from "
            "your Week-1 client — changing only the transport adapter. Maps to: Stops 2–3.")
    st.text_area("Britannia dispute message", SAMPLE, key="a_text", height=90)
    if st.button("Triage it", key="a_run"):
        _render_triage(st.session_state["a_text"])
    exercise("6-A.1 · Prove the hexagon — swap by config only",
             "Deploy a second model and switch by changing `AZURE_OPENAI_DEPLOYMENT` only — no code edit. "
             "Offline, the mock stands in; the point is the **core never changes**.")
    exercise("6-A.2 · Typed triage on a real dispute",
             "Feed the £89.99 sample above and confirm a valid `DisputeTriage` (category, urgency, "
             "needs_human_review, suggested_next_action, pii_detected).")
    scaffold_link("You changed the **transport adapter** only. Port, Pydantic models, retry/timeout are "
                  "byte-for-byte your Week-1 code — the hexagon earning its keep.")
    checkpoint("A validated DisputeTriage from a model in West Europe / UK South, called from your unchanged core.")
    watchout("Region = residency. Choose the EU/UK region at project creation; enable a custom subdomain "
             "(needed for identity auth in 6-B).")


def tab_6b() -> None:
    banner("LAB 6-B · Managed identity · RBAC · remove every API key",
            "Make the call keyless: prove who you are with an identity, not a shared secret. "
            "Maps to: Stop 5.")
    try:
        check = _get("/authcheck").json()
    except Exception as exc:
        _api_down(exc); return
    if check.get("simulated"):
        st.info("**Simulated** — no Azure configured. Below is the posture your live resource would show; "
                "the real proof is: keyless call succeeds, key-based call returns `AuthenticationTypeDisabled`.")
    st.subheader("Keyless checklist")
    st.table([{"check": k, "pass": v} for k, v in check["checklist"].items()])
    st.code(
        'az role assignment create \\\n'
        '  --role "Cognitive Services OpenAI User" \\\n'
        '  --assignee-object-id $PRINCIPAL_ID --assignee-principal-type User --scope $AOAI_ID\n'
        'az rest --method patch --url "https://management.azure.com$AOAI_ID?api-version=2023-05-01" \\\n'
        '  --body \'{"properties":{"disableLocalAuth":true}}\'', language="bash")
    exercise("6-B.1 · Least privilege", "With only `Cognitive Services OpenAI User`, inference works but "
             "deploying a model / viewing keys is blocked. That is least privilege.")
    exercise("6-B.2 · Keyless proof", "After `disableLocalAuth=true`: keyless scaffold succeeds; a key-based "
             "call returns `AuthenticationTypeDisabled`. Paste both outcomes.")
    exercise("6-B.3 · Find the backdoor (stretch)", "Which permission fetches the API key and bypasses RBAC? "
             "Name the **listKeys** action; fix = a custom role (OpenAI User minus listKeys) for humans.")
    scaffold_link("Only the **auth adapter** changed: a 'flaky vendor' your retries already guard is now a "
                  "'trusted-by-identity vendor'. Port, models, retries, timeouts untouched.")
    checkpoint("Zero secrets in the repo; calls succeed by identity; key-based calls blocked at the resource.")
    watchout("Toggling local auth cycles the resource keys — never test on a shared/prod resource other apps use.")


def tab_6c() -> None:
    banner("CHALLENGE 6-C · Replicate the scaffold on Azure — full IAM hardening",
            "Make the setup repeatable & auditable: one Bicep file, keyless from first deploy, "
            "least-privilege RBAC. Maps to: Stops 2–5 combined.")
    st.subheader("infra/main.bicep")
    try:
        with open(os.path.join(os.path.dirname(__file__), "..", "infra", "main.bicep")) as fh:
            st.code(fh.read(), language="bicep")
    except OSError:
        st.warning("infra/main.bicep not found — see Task 10 of the plan.")
    st.subheader("Run the Week-1 contract tests against the active adapter")
    if st.button("Force a 429 burst → show retry recovers (6-C.3)", key="c_run"):
        _render_triage("simulate a transient burst", fail_first_k=2)
        st.caption("attempts > 1 above = retry-with-backoff recovered without crashing the caller.")
    exercise("6-C.2 · Contract tests green on Azure",
             "Run `./.venv/bin/python -m pytest -q` against the Azure adapter — the port contract didn't move.")
    exercise("6-C.4 · Auditor evidence note (stretch)",
             "One paragraph: region, deployment scope, role granted, local auth off, secrets = none.")
    scaffold_link("The entire hexagon on Azure: frozen core, Azure adapters, identity auth, retries/timeouts — "
                  "now reproducible from one Bicep file an auditor can read.")
    checkpoint("az deployment green · contract tests green · zero keys · resource in EU/UK · local auth disabled.")
    watchout("`publicNetworkAccess:'Disabled'` needs a private endpoint to reach the resource. For a laptop lab "
             "set it 'Enabled' + rely on identity; note that production Britannia is private.")


def tab_6d() -> None:
    banner("DRILL 6-D · Latency + cost — Azure OpenAI vs direct OpenAI",
            "Turn your 'Time it out' instrument into a benchmark harness and make the call with data. "
            "Maps to: Stop 6.")
    providers = st.multiselect("Providers to benchmark", ["mock", "azure", "openai"], default=["mock"])
    n = st.slider("Calls per provider (warm-up discarded)", 2, 50, 20)
    if st.button("Run benchmark", key="d_run"):
        try:
            resp = _post("/benchmark", {"providers": providers, "n": n, "dispute_text": SAMPLE})
        except Exception as exc:
            _api_down(exc); return
        if resp.status_code != 200:
            st.error(f"HTTP {resp.status_code}"); st.json(resp.json()); return
        data = resp.json()
        st.table(data["rows"])
        if any(r["simulated"] for r in data["rows"]):
            st.caption("⚠️ Rows marked simulated use **illustrative** latencies (offline mock) — not real measurements.")
        st.success(data["recommendation"])
    exercise("6-D.1/2/3 · Latency · Cost · Recommendation",
             "Fill P50/P95, cost per 1,000 calls (tokens × rate), and the one-line Britannia call.")
    scaffold_link("Your 'Time it out' instrument **is** the benchmark harness — measuring latency now makes a "
                  "procurement decision.")
    watchout("Fair test: same model, same prompts, discard warm-up, don't compare across regions. "
             "Prices/latencies move — record the date + rate you used.")


def tab_capstone() -> None:
    banner("CAPSTONE · Britannia Dispute-Triage Copilot",
            "One small, complete, defensible deliverable: typed · resident · keyless · resilient · "
            "repeatable · benchmarked.")
    st.text_area("Customer dispute (free text)", SAMPLE, key="cap_text", height=90)
    if st.button("Run the copilot", key="cap_run"):
        _render_triage(st.session_state["cap_text"])
    st.subheader("Demonstrate-tomorrow checklist")
    st.table([
        {"#": 1, "show": "A live keyless call returning a validated DisputeTriage", "proves": "Typed + keyless"},
        {"#": 2, "show": "Region + deployment scope, disableLocalAuth = true", "proves": "Residency + identity"},
        {"#": 3, "show": "A forced 429/timeout recovering via retry-with-backoff", "proves": "Resilience (Week-1)"},
        {"#": 4, "show": "main.bicep + the az deployment output", "proves": "Repeatable / auditable"},
        {"#": 5, "show": "Latency + cost table vs direct OpenAI", "proves": "Reasoned decision"},
        {"#": 6, "show": "A 3-sentence 'why Azure for this bank'", "proves": "You can defend the call"},
    ])
    checkpoint("Ready when all six rows run live and your one-page note states region, scope, role, "
               "local-auth-off, and 'secrets: none'.")


def main() -> None:
    st.set_page_config(page_title="Azure Labs 6-A/6-B — Dispute-Triage Copilot", layout="wide")
    st.title("Azure Labs 6-A/6-B · Britannia Dispute-Triage Copilot")
    tabs = st.tabs(["0 · Overview", "1 · 6-A Repoint", "2 · 6-B Keyless",
                    "3 · 6-C Challenge", "4 · 6-D Benchmark", "5 · Capstone"])
    with tabs[0]: tab_overview()
    with tabs[1]: tab_6a()
    with tabs[2]: tab_6b()
    with tabs[3]: tab_6c()
    with tabs[4]: tab_6d()
    with tabs[5]: tab_capstone()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_ui_smoke.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add ui/streamlit_app.py tests/test_ui_smoke.py
git commit -m "feat(6ab): 6-tab Streamlit teaching app (one tab per lab)"
```

---

### Task 10: Bicep artifact (Challenge 6-C IaC)

**Files:**
- Create: `infra/main.bicep`
- Test: `tests/test_bicep.py`

**Interfaces:**
- Produces: a deploy-ready Bicep file with residency param, `disableLocalAuth:true`, `customSubDomainName`, a `gpt-4o-mini` deployment, a user-assigned managed identity, a least-privilege role assignment, and outputs.

- [ ] **Step 1: Write the failing test**

`tests/test_bicep.py`:
```python
import os

BICEP = os.path.join(os.path.dirname(__file__), "..", "infra", "main.bicep")

def test_bicep_exists():
    assert os.path.exists(BICEP)

def test_bicep_hardening_present():
    text = open(BICEP).read()
    assert "disableLocalAuth: true" in text
    assert "customSubDomainName" in text
    assert "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" in text  # Cognitive Services OpenAI User
    assert "userAssignedIdentities" in text
    assert "output endpoint" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_bicep.py -q`
Expected: FAIL (file missing).

- [ ] **Step 3: Write the implementation**

`infra/main.bicep`:
```bicep
// main.bicep  —  Britannia: EU/UK-resident, keyless Azure OpenAI
param location string = 'westeurope'        // residency: EU/UK only
param aoaiName string
param deploymentName string = 'gpt-4o-mini'
var openAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'  // Cognitive Services OpenAI User

resource aoai 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: aoaiName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: aoaiName    // required for Entra ID auth
    disableLocalAuth: true           // keyless only
    publicNetworkAccess: 'Enabled'   // laptop lab; production Britannia = 'Disabled' + private endpoint
  }
}

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aoai
  name: deploymentName
  sku: { name: 'Standard', capacity: 10 }
  properties: { model: { format: 'OpenAI', name: 'gpt-4o-mini', version: '2024-07-18' } }
}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${aoaiName}-app-id'
  location: location
}

resource ra 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aoai.id, uami.id, openAiUserRoleId)
  scope: aoai
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output endpoint string = aoai.properties.endpoint
output deploymentName string = deployment.name
output appClientId string = uami.properties.clientId
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_bicep.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add infra/main.bicep tests/test_bicep.py
git commit -m "feat(6ab): deploy-ready Bicep for keyless EU/UK Azure OpenAI (6-C)"
```

---

### Task 11: Docs + kit pointer + full-suite green

**Files:**
- Create: `README.md`, `00_START_HERE.md`
- Modify: `Azure_Trainee_Lab_Kit.md` (prepend a short "Run the companion app" pointer — leave all lab content unchanged)

**Interfaces:**
- Produces: learner-facing orientation + the link between the markdown kit and the app.

- [ ] **Step 1: Write `00_START_HERE.md`**

```markdown
# Azure Labs 6-A/6-B — Start Here

The runnable companion to `Azure_Trainee_Lab_Kit.md`: a **typed FastAPI wrapper** + **Streamlit UI**
for the Britannia Dispute-Triage Copilot. Runs **fully offline** on a mock provider — no Azure needed.

## Run it (2 commands)

```bash
./setup.sh     # creates .venv, installs, runs the offline-green tests
./run.sh       # API on :8000 + Streamlit on :8501  (override: API_PORT=9000 ./run.sh)
```

Open http://localhost:8501 and walk the tabs left to right.

## Which tab backs which lab

| Tab | Lab | Concept |
|-----|-----|---------|
| 0 · Overview | §0 | auth posture · client/server split |
| 1 · 6-A Repoint | Lab 6-A | deploy + invoke · typed triage · swap-by-config |
| 2 · 6-B Keyless | Lab 6-B | managed identity · RBAC · disableLocalAuth |
| 3 · 6-C Challenge | Challenge | Bicep IaC · contract tests · 429 retry |
| 4 · 6-D Benchmark | Drill | latency + cost · Azure vs direct OpenAI |
| 5 · Capstone | Capstone | the copilot + demonstrate-tomorrow checklist |

## Go live (optional)

Copy `.env.example` to `.env`, set the Azure trio (`AZURE_OPENAI_ENDPOINT` + deployment; key for 6-A,
or `AUTH_MODE=keyless` for 6-B). Restart `./run.sh` — the Overview tab shows the live posture.
```

- [ ] **Step 2: Write `README.md`**

```markdown
# Azure Labs 6-A/6-B — Britannia Dispute-Triage Copilot

Teaching companion for FORGE Batch-1, Day 06-Jul (Azure AI Foundry / IAM). The Week-1 Python
scaffold (typed client · retries · timeouts · hexagonal ports & adapters) pointed at Azure and
hardened around identity. Organising spine: **Type it · Validate it · Retry it · Time it out.**

- **Design:** Streamlit UI → HTTP → FastAPI wrapper → `resilient_triage` → provider
  (mock by default; azure-key / azure-keyless / direct-openai when configured).
- **Offline-first:** every non-optional test and the whole UI work with zero Azure access.
- **Case study:** Britannia Counties Bank — EU/UK residency · keyless · identity-attributable.

## Layout

```
api/    typed FastAPI wrapper (models, errors, client, triage, benchmark, providers)
ui/     Streamlit teaching app (6 tabs — one per lab)
infra/  main.bicep — the 6-C deploy-ready IaC artifact
tests/  pytest — offline-green
```

## Commands

```bash
./setup.sh                         # venv + install + tests
./run.sh                           # API (:8000) + Streamlit (:8501)
./.venv/bin/python -m pytest -q    # tests only
```

> House rule: "works in `.venv`" is a **draft**. Final sign-off is a clean `./setup.sh` + `./run.sh`
> on the Techademy Azure VM.
```

- [ ] **Step 3: Prepend the kit pointer**

Add this block to the very top of `Azure_Trainee_Lab_Kit.md` (above the existing first line — do not change any existing content):

```markdown
> **▶ Run the companion app first.** This kit has a runnable companion in this folder:
> `./setup.sh` then `./run.sh`, open http://localhost:8501. It runs **fully offline** (mock provider)
> so you can rehearse every lab before Azure access lands. Tabs map 1:1 to the labs below
> (Overview · 6-A · 6-B · 6-C · 6-D · Capstone). See `00_START_HERE.md`.

```

- [ ] **Step 4: Run the FULL suite + verify offline-green**

Run: `./.venv/bin/python -m pytest -q`
Expected: PASS — all tests across every module, with no env vars set.

- [ ] **Step 5: Manual smoke (optional but recommended)**

Run: `./run.sh` and confirm all 6 tabs render and the Overview shows `simulated: true`, 6-A returns a validated triage on the £89.99 sample, 6-C shows the Bicep, 6-D shows a simulated table. Ctrl-C to stop.

- [ ] **Step 6: Commit**

```bash
git add README.md 00_START_HERE.md Azure_Trainee_Lab_Kit.md
git commit -m "docs(6ab): start-here + readme + kit pointer to the companion app"
```

---

## Self-Review

**1. Spec coverage:**
- §3 architecture (hexagon, files) → Tasks 1–10. ✓
- §3.1 port → Task 4. ✓ · §3.2 DisputeTriage contract → Task 2. ✓
- §4 six tabs → Task 9 (one renderer each). ✓
- §5 three auth modes + `auth_posture` + simulated labelling → Tasks 5 (posture/adapters) + 9 (UI labelling) + 8 (`/authcheck`). ✓
- §6 error envelope + offline-green tests → Tasks 2,6,8 + every task's tests. ✓
- §7 Bicep → Task 10. ✓
- §9 acceptance (setup green / run / live light-up / bicep valid / kit pointer) → Task 11. ✓

**2. Placeholder scan:** No TBD/TODO; every code step shows complete code. The one prose note in Task 8 explains a real call and offers an equivalent — not a placeholder.

**3. Type consistency:** `TriageRequest`/`ProviderTriageRaw`/`CallOutcome`/`TriageResponse`/`BenchmarkRow` names and fields are consistent across Tasks 2→4→5→6→7→8. `make_provider(..., force_bad_output=...)` matches between Task 5 def and Task 8 use. `auth_posture` keys (`mode/region/custom_subdomain/disable_local_auth/secrets_present/simulated`) consistent across Tasks 5,8,9. `summarize(...)` signature matches Task 7 def and Task 8 call. Provider `.triage()` method name consistent across port, mock, azure, openai, client.

No gaps found.
