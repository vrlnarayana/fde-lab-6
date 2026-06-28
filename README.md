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
