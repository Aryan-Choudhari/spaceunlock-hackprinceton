# SpaceUnlock submission draft

## Tagline

Small changes to existing buildings. More possibilities for the communities around them.

## What it does

SpaceUnlock asks which affordable combination of building changes unlocks the most potential uses. It combines interior measurements and doorway connections from Matterport with exterior parcel evidence from Vexcel, evaluates four community-use templates, and compares every subset of six candidate interventions.

A manager can change the budget, priorities, entrance assumptions or rejected interventions and obtain a new recommendation. Results show source evidence, precise blockers, uncertainty, costs, alternative budgets and a draft approval memo. A local Ollama agent invokes the planning tools and exposes its execution trace.

## How it is built

React and TypeScript provide an interactive floor-plan and planning interface. FastAPI and Pydantic validate scenarios. A deterministic three-state evaluator and graph traversal recompute feasibility for all 64 portfolios. SQLite stores scenarios and approval events. Shapely checks the Vexcel parcel match against the scan coordinates. Ollama runs locally, so the agent requires no OpenAI API key. Matterport tours and cached Vexcel aerial imagery provide visual context.

## Why this is useful

The primary output is the set of additional modeled options enabled by a portfolio under budget. Different uses compete for the same investment, and their requirements interact. The user can inspect why one source, route or budget changes the answer rather than receiving an unsupported narrative recommendation.

## Demonstration

The configured office scenario shows a conditional service-desk option at $5,500, three conditional options at $9,500, and four at $12,000 using simulated intervention costs. Removing a source or blocking access changes the deterministic result. A reviewer can inspect the trace, record a draft decision, export the memo and replay the stored evidence snapshot.

## Tracks supported by the implementation

- Sustainability: explores productive reuse of existing building space; reports candidate room area rather than unsupported carbon savings.
- CoStar ecosystem: Matterport and Vexcel both influence eligibility, with spatial analysis and an inspectable agent workflow.
- Practical AI innovation: local model orchestration with deterministic computation and explicit human review.

LangChain/deepagents and Photon integrations are not included and should not be claimed. Event organizers determine final track eligibility.

## Boundaries

All PASS results for real property scenarios are conditional on explicitly selected operating assumptions. Imagery and scans do not establish accessibility, legal authorization, utility service or actual construction costs. The displayed use options are alternatives, not a simultaneous occupancy plan. Professional review remains necessary.

## Links and materials

Source: https://github.com/Aryan-Choudhari/spaceunlock-hackprinceton

Run instructions: README.md

Presentation script: docs/DEMO.md

Acceptance evidence: docs/ACCEPTANCE.md

The local walkthrough recording and licensed source cache are deliberately excluded from the public repository. Confirm event display rules before uploading a recording containing sponsor data. This draft has not been submitted to an event platform.
