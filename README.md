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

## Lab 6-C — keyless / Bicep test

6-C is the challenge: stand up the whole scaffold on Azure from one Bicep file — keyless from
first deploy, least-privilege RBAC — then prove the contract tests still pass. Test it in two layers.

### Layer 1 — validate locally (no Azure needed)

```bash
./.venv/bin/python -m pytest -q tests/test_bicep.py tests/test_client.py   # 6-C.2 + resilience
az bicep build -f infra/main.bicep --stdout >/dev/null && echo "bicep OK"  # template compiles
```

`test_bicep.py` asserts the hardening is baked in: `disableLocalAuth: true`, `customSubDomainName`,
the *Cognitive Services OpenAI User* role GUID, a user-assigned identity, and `output endpoint`.
For **6-C.3 (survive a burst)**, open the **6-C tab** in the UI → *"Force a 429 burst → show retry
recovers"*. `attempts > 1` = retry-with-backoff recovered without crashing the caller (runs offline
against the mock — it exercises *your* client, not Azure).

### Layer 2 — the real deploy (keyless proof)

```bash
az login
RG=rg-britannia-6c
az group create -n $RG -l westeurope
az deployment group create -g $RG -f infra/main.bicep \
  -p aoaiName=britannia-aoai-<unique> location=westeurope
# capture outputs: endpoint, deploymentName (gpt-4o-mini), appClientId
```

Point the app at it in **keyless** mode — edit `.env`:

```
DEFAULT_PROVIDER=azure
AUTH_MODE=keyless                     # flips the provider to DefaultAzureCredential
AZURE_OPENAI_ENDPOINT=<endpoint output>
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini   # the model the Bicep deploys
# leave AZURE_OPENAI_API_KEY unset — keyless uses your az login identity
```

Restart (`./run.sh`) and verify:

```bash
curl -s localhost:8000/authcheck      # expect mode: keyless, local_auth_disabled: true
```

- **6-C.1 keyless proof:** a triage returns a validated `DisputeTriage` with `auth_mode: keyless`;
  a deliberate key-based call now fails `401 AuthenticationTypeDisabled` — *that failure is the evidence*.
- **6-C.2 on Azure:** rerun `pytest -q` against the live adapter — the port contract didn't move.
- **Checkpoint:** `az deployment` green · contract tests green · zero keys · resource in EU/UK · local auth disabled.

**Watch out**
- **Don't toggle `disableLocalAuth` on a shared/lab-provided resource** — it **rotates the resource keys**
  and breaks any key-based (6-A/6-D) setup still using it. Deploy a *separate* resource for 6-C.
- **Keyless needs RBAC on *your* identity.** The Bicep grants the role to the app's managed identity; for
  local `az login` testing, also grant yourself *Cognitive Services OpenAI User* on the resource
  (`az role assignment create --role "Cognitive Services OpenAI User" --assignee <you> --scope <resourceId>`)
  and allow ~1 min to propagate, or you'll hit a transient 401.
