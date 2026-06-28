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
