# ui/streamlit_app.py
"""Azure Labs 6-A/6-B — Britannia Dispute-Triage Copilot teaching app.

Six tabs, one per lab. Each pairs a LIVE demo with the kit's marks
(banner / exercise / checkpoint / watch-out / Week-1 scaffold link).
A pure HTTP client to the FastAPI wrapper — it never imports the SDKs.
Run the API first (./run.sh does both).
"""
from __future__ import annotations
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
    # 600s: a /benchmark of up to 50 sequential reasoning-model calls (o4-mini/gpt-5
    # run ~5-10s each) can take several minutes; 60s timed out on the 6-D tab.
    return httpx.post(api_url(path), json=payload, timeout=600.0)


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
