# Acceptance evidence and remaining boundaries

Verified locally on November 14, 2026. Engine version 1.1.0. This records demonstrated implementation, not regulatory or sponsor-track approval.

## Implemented P0 scope

| SRS area | Evidence |
| --- | --- |
| FR-01 persistent property | Private sponsor cache loads at restart; synthetic fixture loads without the cache |
| FR-02 two sponsor layers | Matterport room area and Vexcel containing-parcel hardscape are binding checks; source-withholding changes eligibility |
| FR-03 provenance | Source register, observed measurements, explicit approved scenario assumptions, simulated cost basis and unknown checks |
| FR-04 spatial graph | Real commercial scan: the measured rooms and shared doorway connections; authored fixture: 8 nodes and 10 edges |
| FR-05 use templates | Four JSON templates; configurable recursive AND/OR expressions; three-state tests |
| FR-06 interventions | Six JSON interventions with costs, effects, dependencies, exclusions, uncertainty and approval fields |
| FR-07 three states | FAIL / UNKNOWN / PASS with explicit conditional labels for assumption-dependent real outcomes |
| FR-08–09 optimization and reachability | 64 subsets; budget/dependency/exclusion filters; per-portfolio doorway graph traversal; route-block tests |
| FR-10–11 comparison and reproducibility | Baseline/after cards, cost and unlocked-use comparison, saved source snapshot and replay endpoint |
| FR-12 agent tools | Local Ollama selects property context, assess, optimize, compare and draft tools; deterministic validation follows |
| FR-13 grounding | Sources remain data; model cannot modify evidence or approve a plan; numerical outputs use deterministic tools |
| FR-14 export | Markdown and JSON downloads verified in API and browser tests |
| FR-15 recovery | Missing keys and failed connectors return structured errors; missing cache loads fixture; unavailable model falls back with label |

## Acceptance cases

| Case | Verification |
| --- | --- |
| AT-01 fixture load | API fixture test and interactive property selector |
| AT-02 three baseline states | Authored fixture engine test |
| AT-03 insufficient budget | Engine budget cases, including zero and below minimum cost |
| AT-04 $15,000 portfolio | Real office conditional result: $12,000, four use options |
| AT-05 blocked route | Authored and source-backed topology tests recompute reachability |
| AT-06 rejected intervention | Rejection tests; entrance modification becomes an alternative portfolio |
| AT-07 removed measurement | Source-withholding test and real browser interaction produce UNKNOWN |
| AT-08 repeatability | Ten real runs with identical plan facts; stored-plan replay test |
| AT-09 disconnected API | Fixture/no-cache and provider-failure tests; real cached evidence is evaluated without sponsor network calls |
| AT-10 unverified approval | Certification-request denial test; human decision endpoint only records drafts |
| AT-11 memo | API export checks and browser download with sources, blockers, cost basis and gates |
| AT-12 data fusion | Independent source sensitivity tests, plus real source-withholding run |

P1 features include ten-budget comparison, rejected interventions, a clearly labeled room-area reuse proxy, saved scenarios and timestamped decision history.

## Measurements and browser checks

- 27 backend tests passed before final packaging.
- Ten optimizations on the real office cache completed in approximately 0.070 seconds total on this machine.
- A local Ollama five-tool run plus validation completed in approximately seven seconds; this is separate from engine performance.
- Production frontend build passed.
- Fresh public clone: dependency installation, all 27 tests, production build, static startup, fixture loading and optimization passed without private cache or credentials. Hosted CI could not start a runner; it is not marked passing.
- Desktop and 390-pixel mobile browser regressions passed without JavaScript errors or horizontal overflow.
- Browser coverage includes conditional scenario, budget change, approval, memo download, source removal, agent tool ordering and aerial imagery.
- Floor-plan and 3D tour were visually inspected. The tour loaded successfully through normal Matterport sharing permissions.
- Credentials, private source records, the scenario database and recorded demo are Git-ignored. A scan of publishable text found no configured API key/token values.

## Explicit limits and external work

- Actual street-to-floor arrival, entrance function, internal passability, utility availability and operating permissions are assumptions requiring confirmation. External legal and professional gates remain NOT VERIFIED.
- The largest measured room is treated as one candidate space; the four use options are alternatives, not a claim that they can operate simultaneously.
- Hardscape area is an exterior-space screening proxy, not a verified loading zone. Capture dates are exposed and may predate the walkthrough.
- Intervention costs are simulated. The area proxy is not a carbon calculation.
- Real geometric connections come from shared source doorway boundaries. They are not a surveyed accessibility graph.
- Ollama is used directly. LangChain/deepagents and Photon stretch integrations are not claimed.
- No CoStar property extract is used; the two verified sponsor layers are Matterport and Vexcel.
- Public code-only repository: https://github.com/Aryan-Choudhari/spaceunlock-hackprinceton. Event registration/submission and final sponsor review have not been performed.
- The local walkthrough recording is an engineering demo without narration; the two-minute presentation script is in DEMO.md.
