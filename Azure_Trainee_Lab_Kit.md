> **▶ Run the companion app first.** This kit has a runnable companion in this folder:
> `./setup.sh` then `./run.sh`, open http://localhost:8501. It runs **fully offline** (mock provider)
> so you can rehearse every lab before Azure access lands. Tabs map 1:1 to the labs below
> (Overview · 6-A · 6-B · 6-C · 6-D · Capstone). See `00_START_HERE.md`.

**FORGE — FDE ACADEMY**

**Azure for Enterprise AI**

Trainee Lab Kit — hands-on labs, exercises, challenge & capstone

| RUNNING CASE STUDY BFSI — EU-West data-residency landing zone for a UK bank. Every lab uses one scenario: Britannia Counties Bank, a UK retail bank building a customer dispute-triage assistant whose data must never leave the EU/UK boundary, must run keyless, and must stay attributable to an identity. |
| :---- |

This kit plugs your **Week-1 Python scaffold** (typed client · retries · timeouts · hexagonal ports & adapters) into Azure. You are not rebuilding it — you are pointing it at Azure and hardening the identity around it. The organising spine stays the same: **Type it · Validate it · Retry it · Time it out.**

**Trainer** Lakshminarayanan  ·  ArchitectsVibe        **Audience** Senior engineers & architects

**0 · How to use this kit**

Work top to bottom. Each lab is self-contained and builds on the one before. Read the lab **banner** first — it tells you the objective, what it maps to, the tools, and the time budget. Then follow the numbered steps, and stop at every **Exercise** box to actually do the work. Don’t skip the **Checkpoint** boxes — they are how you know a lab is genuinely done.

**How things are marked**

| LAB 0-X This is a lab banner Indigo \= a hands-on lab. Strongly highlighted so you can find it at a glance. Maps to:  the deck stop it belongs to Tools:  the Azure \+ scaffold tools you’ll use      ⏱ \~mm min |
| :---- |

| ✎  EXERCISE 0-X.1 · This is an exercise Amber \= something you must do. Every exercise is numbered LAB.N and listed in the mapping table so you can track completion. |
| :---- |

| ↩  WEEK‑1 SCAFFOLD LINK Lavender \= the link back to your Week-1 Python scaffold — exactly which scaffold concept this Azure step exercises, so the connection is never lost. |
| :---- |

| ✓  CHECKPOINT Green \= the acceptance test. If you can tick this, move on. |
| :---- |

| ⚠  WATCH OUT Red \= a trap that costs people time — read it before it bites you. |
| :---- |

**0.1 · Tools you’ll use**

Every term is explained in plain language on first use. Check each tool is ready before you start Lab 6-A.

| Tool | What it is (plain words) | Check it’s ready |
| :---- | :---- | :---- |
| Azure CLI (az) | The command-line for Azure — you type commands instead of clicking the portal. | az version az login |
| Azure AI Foundry | Microsoft’s unified AI platform (the portal at ai.azure.com). You create a project here. | Open [ai.azure.com](https://ai.azure.com) |
| Azure OpenAI | The OpenAI models (GPT-4o, GPT-4o-mini…) served inside Azure, in your region, under your governance. | Deployed in Lab 6-A |
| Managed Identity | An identity Azure manages for your app, so the app never holds a password or key. | Configured in Lab 6-B |
| Azure RBAC | Role-Based Access Control — the rules for who is allowed to do what (e.g. ‘call the model’ vs ‘deploy a model’). | Used in Lab 6-B |
| Bicep | A small language to declare Azure resources in a file, so your setup is repeatable and reviewable. | az bicep version |
| VS Code Azure ext. | A panel inside VS Code to sign in, browse resources, and deploy — the GUI alternative to the CLI. | Install ‘Azure Tools’ in VS Code |
| Week-1 scaffold | Your typed, retried, timed-out Python LLM client with hexagonal ports & adapters. | Clone your repo locally |

**0.2 · Before you start — prerequisites**

* An Azure subscription with access to **Azure OpenAI / Foundry** (approved), plus a resource group you can deploy into.

* Permission to **create resources and assign RBAC roles** (Owner or User Access Administrator on the resource group), or a sandbox where this is pre-granted.

* Python 3.11+, your Week-1 scaffold repo, the openai and azure-identity packages, and VS Code with the Azure Tools extension.

| ⚠  WATCH OUT Licence & access is the \#1 blocker. Azure OpenAI/Foundry access approval and the right to assign roles are often gated by your platform team. Confirm both before the session — not during it. |
| :---- |

**0.3 · The running case study — Britannia Counties Bank**

**Scenario.**  Britannia Counties Bank (a fictional UK retail bank) is building a **Dispute-Triage Copilot**. A customer types a free-text message about a card transaction they don’t recognise; the assistant returns a **typed triage**: category, urgency, whether a human must review, the suggested next action, and whether the text contains PII to redact before logging.

**Hard constraints (from the bank’s risk team).**

| Constraint | What it means | Azure answer you’ll build |
| :---- | :---- | :---- |
| Data residency | Customer PII & transaction data must not leave the EU/UK boundary. | Region in West Europe / UK South \+ EU Data-Zone deployment scope (Lab 6-A) |
| No keys | No long-lived secrets in code or config — every call must be attributable to an identity. | Managed identity \+ least-privilege RBAC \+ disableLocalAuth (Lab 6-B) |
| Resilience | A provider hiccup (429/timeout) must never crash the customer journey. | Your Week-1 retries \+ timeouts (used throughout) |
| Typed output | Downstream systems need a strict, validated shape — not free text. | Your Week-1 Pydantic models (unchanged) |
| Repeatable | An auditor must be able to see the setup was deployed the same way every time. | Bicep infrastructure-as-code (Challenge) |

**This is your Week-1 scaffold’s exact job** — now wrapped in Azure’s residency and identity envelope. Keep Britannia in mind in every lab.

**Exercise map — lab × Azure concept × scaffold concept**

Use this as your completion tracker. Every exercise links an Azure skill to a Week-1 scaffold idea.

| Exercise | Lab | Azure concept | Week-1 scaffold concept |
| :---- | :---- | :---- | :---- |
| 6-A.1 | 6-A | Model catalogue · deployment | Hexagonal: swap adapter by config, core unchanged |
| 6-A.2 | 6-A | Invoke a deployment endpoint | Typed client · Pydantic validation |
| 6-B.1 | 6-B | Least-privilege RBAC role | Adapter boundary · capability, not credentials |
| 6-B.2 | 6-B | disableLocalAuth (keyless) | Auth adapter swap: key → identity |
| 6-B.3 | 6-B | listKeys backdoor · custom role | Defence in depth around the port |
| 6-C.1–4 | Challenge | Bicep · full IAM hardening | Whole hexagon on Azure · contract tests · retries |
| 6-D.1–3 | Drill | Azure OpenAI vs direct OpenAI | ‘Time it out’ instrument → benchmark harness |
| Capstone | Homework | Residency \+ identity end-to-end | The complete scaffold, demonstrated |

**Week-1 scaffold — 60-second recap**

Today’s labs touch only the edges of this picture. The **core stays frozen**; you repoint adapters and tighten identity.

| Scaffold piece | What it does | What changes today |
| :---- | :---- | :---- |
| Port: LLMClient | An interface your core depends on — ‘give a prompt, get a typed result’. | Nothing. The contract is stable. |
| Adapter (transport) | Implements the port for one provider (endpoint, request shape). | Repoint to an Azure OpenAI deployment (6-A). |
| Adapter (auth) | How the adapter proves who it is. | Swap API key → managed identity (6-B). |
| Pydantic models | Typed request/response — validate every reply. | Nothing. Reused as-is. |
| Retry \+ timeout | Guards around the ‘flaky vendor’ call. | Now also catch Azure 429 / quota bursts. |
| Contract tests | Assert the adapter honours the port. | Run them green against Azure (Challenge). |

| ↩  WEEK‑1 SCAFFOLD LINK The hexagonal payoff in one line: because your core depends on a port, not a provider, ‘move to Azure’ is an adapter change — not a rewrite. Labs 6-A and 6-B are precisely that adapter change. |
| :---- |

| LAB 6-A Create a Foundry project · deploy a model · invoke from your scaffold Stand up an Azure OpenAI deployment in your residency region and call it from your Week-1 client. Maps to:  Stop 2 (Foundry) \+ Stop 3 (Azure OpenAI) Tools:  Azure AI Foundry · Azure OpenAI · VS Code Azure ext. · Python scaffold      ⏱ 40 min |
| :---- |

**Objective**

Create a Foundry project in an **EU/UK region** (residency starts here), deploy a small model, and get a **typed triage** back from your existing scaffold — changing only the transport adapter.

**Steps**

**1**  Sign in. Open ai.azure.com in the browser, and in a terminal run az login. In VS Code, open the **Azure** panel and sign in too — that’s your GUI view of everything you create.

**2**  Create a project. In Foundry, choose **Create new → project**. When asked for a region, pick **West Europe** or **UK South** — this is the residency decision for Britannia. A project is your workspace; it sits inside a hub that holds shared settings.

**3**  Deploy a model. In your project, open the **model catalogue**, pick gpt-4o-mini (right-sized and cheap — triage is a simple task), and click **Deploy**. Note two things: the **deployment name** you chose, and the **endpoint** URL.

**4**  Smoke test (temporary key). For this first call only, copy the resource key from **Keys and Endpoint**. You will delete it in Lab 6-B — it exists here purely to prove the pipe works.

**5**  Repoint your adapter. In your scaffold, set the Azure adapter’s endpoint and deployment name, and call it with your existing Pydantic models, retry and timeout. The minimum:

| *Only the transport changed — models, retry and timeout are your Week-1 code.* \# adapters/azure\_openai\_adapter.py  (temporary key version) from openai import AzureOpenAI client \= AzureOpenAI(     azure\_endpoint=settings.AZURE\_OPENAI\_ENDPOINT,   \# https://\<resource\>.openai.azure.com/     api\_key=settings.AZURE\_OPENAI\_KEY,               \# REMOVED in Lab 6-B     api\_version="2024-10-21", ) resp \= client.chat.completions.create(     model=settings.AZURE\_OPENAI\_DEPLOYMENT,          \# deployment name, NOT the model id     messages=build\_messages(dispute\_text),     timeout=10,                                       \# 'Time it out' ) triage \= DisputeTriage.model\_validate\_json(resp.choices\[0\].message.content)  \# 'Validate it' |
| :---- |

**6**  Run your existing CLI/test entry-point against a sample Britannia dispute message and confirm you get a valid DisputeTriage object.

| ✎  EXERCISE 6-A.1 · Prove the hexagon — swap by config only Deploy a second model (e.g. gpt-4o). Switch your adapter to it by changing AZURE\_OPENAI\_DEPLOYMENT only — no code edit. Confirm both run. Deliver: the two deployment names and one sentence on why no core code changed. |
| :---- |

| ✎  EXERCISE 6-A.2 · Typed triage on a real dispute Feed this message through your scaffold: *“I was charged £89.99 by ‘GLOBL-SVC’ twice on 3 June, I never authorised it.”* Deliver: the validated DisputeTriage JSON (category, urgency, needs\_human\_review, suggested\_next\_action, pii\_detected). Pydantic validation must pass. |
| :---- |

| ↩  WEEK‑1 SCAFFOLD LINK You changed the transport adapter only. The port, the Pydantic models, and the retry/timeout guards are byte-for-byte your Week-1 code. That is the hexagonal architecture earning its keep. |
| :---- |

| ✓  CHECKPOINT You get a validated DisputeTriage from a model running in West Europe / UK South, called from your unchanged core. |
| :---- |

| ⚠  WATCH OUT Region \= residency. Choose the EU/UK region at project creation; you can’t casually move data later. And enable a custom subdomain on the resource — identity-based auth in Lab 6-B requires it (the portal does this for you when you create an Azure OpenAI resource). |
| :---- |

| LAB 6-B Managed identity · grant RBAC · remove every API key Make the call keyless: prove who you are with an identity, not a shared secret. Maps to:  Stop 5 (Managed identities & RBAC — never use API keys) Tools:  Azure CLI · Managed Identity · Azure RBAC · VS Code Azure ext.      ⏱ 40 min |
| :---- |

**Objective**

Replace the API key in your adapter with **DefaultAzureCredential**, grant your identity the least-privilege role, then **disable key auth entirely** so a leaked key can never be used again.

**Steps**

**1**  Find your identity. For local dev, DefaultAzureCredential uses your az login session. Capture your object id:

| PRINCIPAL\_ID=$(az ad signed-in-user show \--query id \-o tsv) AOAI\_ID=$(az cognitiveservices account show \-g $RG \-n $AOAI \--query id \-o tsv) |
| :---- |

**2**  Grant least privilege. Assign only Cognitive Services OpenAI User — enough to call the model, nothing more:

| az role assignment create \\   \--role "Cognitive Services OpenAI User" \\   \--assignee-object-id $PRINCIPAL\_ID \\   \--assignee-principal-type User \\   \--scope $AOAI\_ID \# (allow \~5 min to take effect) |
| :---- |

**3**  Go keyless in code. Delete api\_key and authenticate with a token provider:

| *DefaultAzureCredential \= az login locally, managed identity in production. Same code.* \# adapters/azure\_openai\_adapter.py  (keyless — final) from azure.identity import DefaultAzureCredential, get\_bearer\_token\_provider from openai import AzureOpenAI   token \= get\_bearer\_token\_provider(     DefaultAzureCredential(),     "https://cognitiveservices.azure.com/.default",   \# the OpenAI token scope ) client \= AzureOpenAI(     azure\_endpoint=settings.AZURE\_OPENAI\_ENDPOINT,     azure\_ad\_token\_provider=token,                    \# identity, not a secret     api\_version="2024-10-21", ) \# same .chat.completions.create(...) call as before — nothing else changes |
| :---- |

**4**  Scrub the secret. Remove AZURE\_OPENAI\_KEY from .env, code and history. There should be **no secret anywhere** in the repo.

**5**  Lock the door. Disable key auth on the resource so keys simply stop working:

| az rest \--method patch \\   \--url "https://management.azure.com$AOAI\_ID?api-version=2023-05-01" \\   \--body '{"properties":{"disableLocalAuth":true}}' \# enforce tenant-wide later with Azure Policy (Audit \-\> Deny) |
| :---- |

**6**  Re-run your scaffold — it works keyless. Then try a key-based call — it now fails with AuthenticationTypeDisabled. That failure is the proof.

| ✎  EXERCISE 6-B.1 · Least privilege, demonstrated With only the OpenAI User role, attempt to deploy a new model or view keys in the portal. Deliver: a note that both are blocked — inference works, management does not. That is least privilege. |
| :---- |

| ✎  EXERCISE 6-B.2 · Keyless proof After disableLocalAuth=true, run (a) your keyless scaffold and (b) a deliberate key-based call. Deliver: (a) succeeds; (b) returns AuthenticationTypeDisabled. Paste both outcomes. |
| :---- |

| ✎  EXERCISE 6-B.3 · Find the backdoor (stretch) Which permission lets a role holder fetch the API key and bypass all your RBAC? Explain why, and propose a fix for human users. Deliver: name the listKeys action and a one-line custom-role plan (User role minus listKeys). |
| :---- |

| ↩  WEEK‑1 SCAFFOLD LINK Only the auth adapter changed: the ‘flaky vendor’ your retries already guard is now a ‘trusted-by-identity vendor’. The port, models, retries and timeouts are untouched — the same lesson as ‘never put keys in the frontend’, scaled up to ‘never hold keys at all’. |
| :---- |

| ✓  CHECKPOINT Zero secrets in the repo; calls succeed by identity; key-based calls are blocked at the resource. |
| :---- |

| ⚠  WATCH OUT Toggling local auth cycles the keys. Turning disableLocalAuth off and on again rotates the resource keys — never test this on a shared or production resource that other apps still call with keys. |
| :---- |

| CHALLENGE 6-C Replicate the Week-1 scaffold on Azure — full IAM hardening Stand up the whole scaffold against Azure from infrastructure-as-code, hardened end to end. Maps to:  Stops 2–5 combined · the complete hexagon Tools:  Bicep · Azure CLI · Managed Identity · Azure RBAC · VS Code Azure ext.      ⏱ 60–90 min |
| :---- |

**Objective**

Make the setup **repeatable and auditable**: declare the Azure OpenAI resource, a deployment, a user-assigned managed identity, and a least-privilege role assignment in one Bicep file — keyless from the first deploy — then run your contract tests green against it.

**Steps**

**1**  Save the template below as main.bicep. It bakes in residency (region param), keyless (disableLocalAuth:true), and least-privilege RBAC.

| // main.bicep  —  Britannia: EU/UK-resident, keyless Azure OpenAI param location string \= 'westeurope'        // residency: EU/UK only param aoaiName string param deploymentName string \= 'gpt-4o-mini' var openAiUserRoleId \= '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'  // Cognitive Services OpenAI User   resource aoai 'Microsoft.CognitiveServices/accounts@2024-10-01' \= {   name: aoaiName   location: location   kind: 'OpenAI'   sku: { name: 'S0' }   properties: {     customSubDomainName: aoaiName    // required for Entra ID auth     disableLocalAuth: true           // keyless only     publicNetworkAccess: 'Disabled'  // pair with a private endpoint in the real LZ   } }   resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' \= {   parent: aoai   name: deploymentName   sku: { name: 'Standard', capacity: 10 }   properties: { model: { format: 'OpenAI', name: 'gpt-4o-mini', version: '2024-07-18' } } }   resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' \= {   name: '${aoaiName}-app-id'   location: location }   resource ra 'Microsoft.Authorization/roleAssignments@2022-04-01' \= {   name: guid(aoai.id, uami.id, openAiUserRoleId)   scope: aoai   properties: {     roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)     principalId: uami.properties.principalId     principalType: 'ServicePrincipal'   } }   output endpoint string \= aoai.properties.endpoint output deploymentName string \= deployment.name output appClientId string \= uami.properties.clientId |
| :---- |

**2**  Deploy it (CLI or the VS Code ‘Deploy to Azure’ right-click):

| az deployment group create \-g $RG \-f main.bicep \\   \-p aoaiName=britannia-aoai location=westeurope |
| :---- |

**3**  Wire your scaffold to the outputs: endpoint, deploymentName, and — when running under the app identity — set AZURE\_CLIENT\_ID to appClientId so DefaultAzureCredential uses the user-assigned identity.

**4**  Run your Week-1 **contract tests** against the Azure adapter. They should pass unchanged — the port contract didn’t move.

| ✎  EXERCISE 6-C.1 · Confirm keyless at the resource From the deployed resource, prove disableLocalAuth is true and a key-based call fails. Deliver: one screenshot or CLI output. |
| :---- |

| ✎  EXERCISE 6-C.2 · Contract tests green on Azure Run your full Week-1 contract-test suite. Deliver: a green test summary against the Azure adapter. |
| :---- |

| ✎  EXERCISE 6-C.3 · Survive a burst Force a transient failure (a tiny timeout, or simulate a 429\) and show your retry-with-backoff recovers without crashing the caller. Deliver: the log showing retry → success. |
| :---- |

| ✎  EXERCISE 6-C.4 · Auditor evidence note (stretch) Write one paragraph an auditor would accept: region, deployment scope, role granted, local auth off, secrets \= none. Deliver: the paragraph. |
| :---- |

| ↩  WEEK‑1 SCAFFOLD LINK This is the entire hexagon on Azure: frozen core, Azure adapters, identity-based auth, retries and timeouts intact — and now reproducible from one Bicep file an auditor can read. |
| :---- |

| ✓  CHECKPOINT az deployment green · contract tests green · zero keys · resource in EU/UK · local auth disabled. |
| :---- |

| ⚠  WATCH OUT publicNetworkAccess: 'Disabled' means you need a private endpoint to actually reach the resource — that’s the real Britannia landing zone. For the lab on a laptop, set it to 'Enabled' and rely on identity; note clearly in your evidence that production would be private. |
| :---- |

| DRILL 6-D Latency \+ cost benchmark — Azure OpenAI vs direct OpenAI Turn your ‘Time it out’ instrument into a benchmark harness and make the call with data. Maps to:  Stop 6 (the decision) Tools:  Python scaffold · Azure OpenAI · direct OpenAI · VS Code      ⏱ 30 min |
| :---- |

**Objective**

Run the same prompts against the same model family on both providers, measure **latency and cost**, and write a recommendation grounded in Britannia’s constraints — not vibes.

**Steps**

**1**  Reuse the timing wrapper you already built for timeouts to record per-call latency and token usage (resp.usage).

**2**  Send **20 identical** Britannia dispute prompts to (a) your Azure gpt-4o-mini deployment and (b) direct OpenAI gpt-4o-mini. Discard the first (warm-up) call.

**3**  Record P50 and P95 latency, average tokens, and cost per call (tokens × published rate). Fill the table:

| Metric | Azure OpenAI | Direct OpenAI | Note |
| :---- | :---- | :---- | :---- |
| P50 latency (ms) | … | … | median — typical call |
| P95 latency (ms) | … | … | tail — worst 1 in 20 |
| Avg tokens / call | … | … | in \+ out |
| Cost / 1,000 calls | … | … | tokens × rate (+ Azure add-ons, noted) |
| Residency | EU/UK region | US default | the deciding constraint |
| Auth | keyless (identity) | API key | audit posture |

| ✎  EXERCISE 6-D.1 · Latency Fill P50 and P95 for both over your 20 calls. Deliver: the four numbers \+ one line on the tail. |
| :---- |

| ✎  EXERCISE 6-D.2 · Cost Compute cost per 1,000 calls for both from token usage × current rate; note Azure’s enterprise add-ons qualitatively. Deliver: the two figures \+ the add-on caveat. |
| :---- |

| ✎  EXERCISE 6-D.3 · The recommendation Write the one-line call for Britannia using your data and the residency/identity constraints. Deliver: the recommendation — expect Azure to win on the envelope even at latency/price parity. |
| :---- |

| ↩  WEEK‑1 SCAFFOLD LINK Your ‘Time it out’ instrument is the benchmark harness. Measuring latency was always part of the scaffold — here it makes a procurement decision. |
| :---- |

| ⚠  WATCH OUT Make it a fair test. Same model, same prompts, discard warm-up calls, and don’t compare across regions. Latency and price numbers are indicative and move — record the date and rate you used. |
| :---- |

| CAPSTONE HOMEWORK Britannia Dispute-Triage Copilot — build, then demo tomorrow Put it all together into one small, complete, defensible deliverable and present it next day. Maps to:  Everything · residency \+ identity end-to-end Tools:  Foundry · Azure OpenAI · Azure CLI · Managed Identity · RBAC · Bicep · VS Code      ⏱ post-session |
| :---- |

**The brief**

For **Britannia Counties Bank**, deliver a working **Dispute-Triage Copilot** that takes a customer’s free-text dispute and returns a validated triage — built on your Week-1 scaffold, on Azure, the right way:

* **Typed & validated** — Week-1 Pydantic models; every reply validated.

* **Resident** — Azure OpenAI in West Europe / UK South with a residency-appropriate deployment scope.

* **Keyless** — managed identity \+ Cognitive Services OpenAI User \+ disableLocalAuth.

* **Resilient** — retries \+ timeouts; a forced 429 recovers cleanly.

* **Repeatable** — provisioned from your main.bicep.

* **Benchmarked** — a 10-call latency/cost note vs direct OpenAI.

**The expected output shape**

| \# models.py  —  the typed contract your copilot must return from enum import Enum from pydantic import BaseModel, Field   class Urgency(str, Enum):     low \= 'low'; medium \= 'medium'; high \= 'high'   class DisputeTriage(BaseModel):     category: str \= Field(..., description='card\_fraud | duplicate\_charge | subscription | atm | other')     urgency: Urgency     needs\_human\_review: bool     suggested\_next\_action: str     pii\_detected: bool \= Field(..., description='true if text holds PII to redact before logging') |
| :---- |

**Demonstrate tomorrow — a 3-minute demo \+ a 1-page evidence note**

Bring these and be ready to run them live:

| \# | Show this | Proves |
| :---- | :---- | :---- |
| 1 | A live keyless call returning a validated DisputeTriage | Typed \+ keyless |
| 2 | The resource’s region \+ deployment scope, and disableLocalAuth \= true | Residency \+ identity |
| 3 | A forced 429/timeout recovering via retry-with-backoff | Resilience (Week-1) |
| 4 | main.bicep \+ the az deployment output | Repeatable / auditable |
| 5 | Your latency \+ cost table vs direct OpenAI | Reasoned decision |
| 6 | A 3-sentence ‘why Azure for this bank’ | You can defend the call |

| ✓  CHECKPOINT You’re ready when all six rows above run live and your one-page evidence note states region, scope, role, local-auth-off, and ‘secrets: none’. |
| :---- |

| ▸  TIP Stuck on access? Build everything you can with the temporary-key version from Lab 6-A, then layer identity on top — but your demo’s headline claim must be keyless, so prioritise getting RBAC working. |
| :---- |

**Appendix — quick reference**

**A.1 · Command cheat-sheet**

| az login az group create \-n $RG \-l westeurope \# create keyless-capable Azure OpenAI (custom subdomain on) az cognitiveservices account create \-g $RG \-n $AOAI \-l westeurope \\   \--kind OpenAI \--sku S0 \--custom-domain $AOAI \--yes \# deploy a model az cognitiveservices account deployment create \-g $RG \-n $AOAI \\   \--deployment-name gpt-4o-mini \--model-name gpt-4o-mini \\   \--model-version 2024-07-18 \--model-format OpenAI \\   \--sku-name Standard \--sku-capacity 10 \# least-privilege role az role assignment create \--role "Cognitive Services OpenAI User" \\   \--assignee-object-id $PRINCIPAL\_ID \--assignee-principal-type User \--scope $AOAI\_ID \# turn keys off az rest \--method patch \--url "https://management.azure.com$AOAI\_ID?api-version=2023-05-01" \\   \--body '{"properties":{"disableLocalAuth":true}}' |
| :---- |

**A.2 · RBAC roles you’ll meet**

| Role | Use it for | Can it call the model? |
| :---- | :---- | :---- |
| Cognitive Services OpenAI User | Apps & service identities — inference only | Yes (least privilege) |
| Cognitive Services OpenAI Contributor | People who deploy / fine-tune models | Yes \+ manage |
| Cognitive Services Usages Reader | Viewing quota | No — read quota only |
| Any role with listKeys | Avoid for humans — it can fetch the API key | Bypasses RBAC — backdoor |

**A.3 · Troubleshooting**

| Symptom | Likely cause | Fix |
| :---- | :---- | :---- |
| 401 AuthenticationTypeDisabled | Keys are off; you sent an api\_key | Use DefaultAzureCredential (keyless) |
| 403 / PermissionDenied | Identity lacks the role | Grant Cognitive Services OpenAI User; wait \~5 min |
| 429 Too Many Requests | TPM/RPM or PTU exhausted | Retry+backoff; request quota; multi-region; spillover |
| Entra auth won’t enable | No custom subdomain on resource | Recreate with \--custom-domain / customSubDomainName |
| Data in wrong geography | Global scope or US region chosen | Use EU/UK region \+ Data-Zone/Regional scope |

| ⚠  WATCH OUT Accuracy & currency. Azure moves fast. Model names, prices, regional availability, role names and API versions (e.g. 2024-10-01, 2023-05-01) all change — confirm against the live Azure docs before you rely on a command in production. This kit teaches the method and the guardrails, which are stable; treat the exact strings as examples to verify, not gospel. |
| :---- |

*— End of Trainee Lab Kit —*