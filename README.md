# SpaceUnlock

Find the smallest affordable set of building changes that unlocks more potential uses. SpaceUnlock combines Matterport room measurements and doorway topology with Vexcel exterior property evidence, a deterministic feasibility engine, exhaustive portfolio optimization, and a local Ollama agent.

## Start

Python 3.10+ and Node 20+ are required.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # only on first setup; preserve existing credentials
cd frontend
npm install
npm run build
cd ..
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://localhost:8000**. API reference: `/docs`. For UI development run `npm run dev` inside `frontend`, with the backend running.

## Real sponsor data

The local private cache contains a verified coordinate match for a commercial Houston office selected through the authorized model browser, with measured rooms and shared doorway connections, and Vexcel parcel records. It is excluded from Git. On a fresh checkout, the synthetic fixture works immediately. To fetch the real dataset with your own authorized sponsor credentials:

```bash
.venv/bin/python -m scripts.ingest --model-id YOUR_AUTHORIZED_MODEL_ID
```

The importer validates that a Vexcel parcel contains the scan coordinates before replacing the cache. It fetches room measurements, wall boundaries and door openings. The planner uses the newest returned containing-parcel capture. Area units are converted explicitly. The floor drawing uses actual source wall geometry. Shared doorway topology does not certify passability or entrance function.

Matterport and Vexcel credentials live only in the backend. Set `MATTERPORT_API_KEY`, `MATTERPORT_API_TOKEN`, and `VEXCEL_API_KEY` in `.env`. Model search is in Evidence; `MATTERPORT_MODEL_ID` is optional. `MATTERPORT_SDK_KEY` is reserved for future scripted viewer controls; current tours open using normal Matterport sharing links and require no SDK key.

Data is cached for offline presentation. If the cache is absent, the app provides the clearly labeled synthetic fixture. Source-withholding controls demonstrate how missing data changes results to UNKNOWN. Raw sponsor evidence, images, scenarios and credentials must stay out of a public repository.

## Local agent

No OpenAI key is required. Run Ollama locally with `llama3.2:1b` installed:

```bash
ollama serve
ollama pull llama3.2:1b
```

The agent selects actions through schema-constrained JSON and invokes real property context, assessment, optimization, comparison and draft tools. Tool dependencies are enforced server-side. Every execution is recorded in the trace. Numerical results come from deterministic tools. The local model never approves a plan or changes source evidence. Optional `OLLAMA_MODEL` and `OLLAMA_BASE_URL` override defaults. If OpenAI credentials are configured, the OpenAI tool-calling implementation is used. If the provider is unavailable, the app labels its deterministic fallback.

## Planning model

- Four templates and six interventions are stored in `data/use_templates.json` and `data/interventions.json`.
- A recursive AND/OR evaluator implements PASS / FAIL / UNKNOWN semantics.
- All 64 portfolios are evaluated or rejected for budget, dependencies or incompatibilities.
- Ranking maximizes weighted newly unlocked uses, then minimizes cost, intervention count as an uncertainty proxy, and sorted intervention IDs.
- Real routes are recomputed through the shared-doorway graph for each candidate. Entry function and passability require explicit scenario assumptions.
- The service desk can use an existing available room. Workshop and coworking require room reassignment. Distribution also requires the exterior hardscape screening threshold and explicit pickup permission.
- Baseline unknowns are never silently turned into source facts. A conditional PASS depends on the checked assumptions, with external gates still NOT VERIFIED.
- Intervention costs are simulated, not quotes. Hardscape area is only an exterior-area proxy; it does not prove loading access. Reuse impact is candidate room area counted once, not CO2 savings.

## Demo

See [the two-minute demo](docs/DEMO.md) and [acceptance evidence](docs/ACCEPTANCE.md). The core real scenario uses explicit assumptions and a $15,000 budget, yielding a $12,000 plan for four conditional uses. A $5,500 budget can support a conditional service desk. At $9,500, three uses pass conditionally; adding the $2,500 pickup-zone intervention unlocks conditional distribution. Street-to-floor arrival, operating permission and internal passability all require explicit assumptions. The fixture remains available for an authored baseline with all three status categories.

Use Evidence to inspect source values, dates and references, load the cached aerial image, browse models, and withhold source layers. Use Saved scenarios to restore a scenario for the current property. Approve draft / Reject / Revise records timestamped audit events. Export Markdown or JSON from the result.

## Verification

```bash
.venv/bin/python -m pytest -q
cd frontend
npm run build
npx playwright install chromium
node e2e/demo.mjs
```

The browser script requires the local server, authorized private cache, and local Ollama. It covers real geometry, conditional planning, approval, local agent trace, evidence, desktop and mobile. Screenshots are written to `/tmp`. Unit tests use authored fixtures and never require sponsor credentials.

## Scope and limits

This is a local, trusted-user hackathon application, not an authenticated multiuser deployment. Legal approval, construction execution, Photon messaging and a LangChain/deepagents implementation are not included. The local agent uses direct Ollama structured calls. CoStar property-extract integration is not claimed: the two real sponsor layers are Matterport and Vexcel. Professional review and operator confirmation remain essential, and the app does not replace them.

A local Git repository is initialized and the source is ready for publication, but GitHub publication, event submission and sponsor permission to publicly display licensed evidence remain separate external steps. Cached sponsor data is not distributed with source.

The pinned Python environment used for verification is recorded in `requirements-lock.txt`. The recorded local walkthrough is `docs/private/spaceunlock-demo.webm` (ignored because it displays sponsor data). Saved recommendations expose a **Verify reproducibility** action that replays their source snapshot.
