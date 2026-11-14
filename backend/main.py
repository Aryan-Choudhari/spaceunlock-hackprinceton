import itertools, json, os, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from backend.rules import all_checks, evaluate

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="SpaceUnlock", version="1.0.0")
VERSION = "1.1.0"
NODES = [
    {"id": x, "x": a, "y": b}
    for x, a, b in [
        ("street", 40, 160),
        ("entrance_A", 150, 80),
        ("lobby", 280, 80),
        ("hall", 410, 160),
        ("flex", 550, 80),
        ("office", 550, 240),
        ("entrance_B", 280, 300),
        ("loading", 40, 300),
    ]
]
EDGES = [
    ("street", "entrance_A"),
    ("entrance_A", "lobby"),
    ("lobby", "hall"),
    ("hall", "flex"),
    ("hall", "office"),
    ("street", "entrance_B"),
    ("entrance_B", "hall"),
    ("street", "loading"),
    ("loading", "entrance_B"),
    ("lobby", "office"),
]
INTERVENTIONS = json.loads((ROOT / "data/interventions.json").read_text())
USES = json.loads((ROOT / "data/use_templates.json").read_text())
BUILDING = {
    "building_id": "DEMO-HOU-001",
    "name": "The Franklin Annex",
    "location": "Houston · synthetic demonstration",
    "data_mode": "fixture",
    "is_synthetic": True,
    "area_sqm": 420,
    "spaces": NODES,
    "graph": {
        "nodes": NODES,
        "edges": [{"id": a + "_to_" + b, "from": a, "to": b} for a, b in EDGES],
    },
    "evidence": [
        {
            "evidence_id": "fixture-layout",
            "status": "synthetic",
            "source_type": "manual fixture",
            "observation": "Authored room connectivity; no real property observations.",
        },
        {
            "evidence_id": "fixture-interventions",
            "status": "estimated",
            "source_type": "manual fixture",
            "observation": "Simulated intervention effects and costs.",
        },
    ],
}


class Scenario(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    building_id: str = "DEMO-HOU-001"
    entry_room_id: str | None = None
    assumptions: dict[str, bool] = Field(default_factory=dict)
    withheld_sources: list[Literal["matterport", "vexcel"]] = Field(
        default_factory=list
    )
    budget_usd: float = Field(default=15000, ge=0, le=10000000)
    use_weights: dict[str, float] = Field(default_factory=dict)
    disabled_edges: list[str] = Field(default_factory=list)
    rejected_interventions: list[str] = Field(default_factory=list)
    request_text: str = Field(default="", max_length=1000)
    name: str = Field(default="Untitled scenario", max_length=100)


class Decision(BaseModel):
    decision: Literal["approved_draft", "rejected", "revise"]


def validate(s):
    from backend.realdata import context

    allowed = {a + "_to_" + b for a, b in EDGES}
    if s.building_id != "DEMO-HOU-001" and context():
        allowed |= {e["id"] for e in context()["graph"]["edges"]}
    if set(s.disabled_edges) - allowed:
        raise HTTPException(422, "Unknown graph edge")
    if set(s.rejected_interventions) - {i["id"] for i in INTERVENTIONS}:
        raise HTTPException(422, "Unknown intervention")
    if set(s.use_weights) - {u["id"] for u in USES} or any(
        not 0 <= v <= 100 for v in s.use_weights.values()
    ):
        raise HTTPException(422, "Invalid use weights")


def assess(s, selected=()):
    validate(s)
    if s.building_id != "DEMO-HOU-001":
        from backend import realdata

        if not realdata.context() or s.building_id != realdata.context()["building_id"]:
            raise HTTPException(404, "Building unavailable")
        if set(s.assumptions) - set(realdata.ASSUMPTIONS):
            raise HTTPException(422, "Unknown assumption")
        return realdata.assess(s, selected, USES)
    active = {a + "_to_" + b for a, b in EDGES} - {
        "street_to_entrance_B",
        "loading_to_entrance_B",
        "hall_to_flex",
    }
    caps = {"flex_area": 30, "hours": True, "power": None, "pickup": False}
    for i in selected:
        active.update(i["edges"])
        caps.update(i["effects"])
    active -= set(s.disabled_edges)
    reached = {"street"}
    for _ in NODES:
        for a, b in EDGES:
            if a + "_to_" + b in active and (a in reached or b in reached):
                reached.update([a, b])
    results = []
    for u in USES:
        checks = []
        for k, v in u["requirements"]:
            actual = (
                k.split(":")[1] in reached if k.startswith("route:") else caps.get(k)
            )
            status = (
                "UNKNOWN"
                if actual is None
                else (
                    "PASS"
                    if (actual == v if isinstance(v, bool) else actual >= v)
                    else "FAIL"
                )
            )
            checks.append(
                {
                    "capability": k,
                    "required": v,
                    "actual": actual,
                    "status": status,
                    "source_refs": ["fixture-layout"],
                    "provenance": "unknown" if actual is None else "synthetic",
                }
            )
        expression = u.get("requirement_expression") or {
            "op": "AND",
            "children": [{"check": i} for i in range(len(checks))],
        }
        status = evaluate(expression, checks)
        results.append(
            {
                **u,
                "status": status,
                "checks": checks,
                "requirement_expression": expression,
                "external_gate": u["gate"] + " — NOT VERIFIED",
            }
        )
    return {
        "uses": results,
        "active_edges": sorted(active),
        "reachable_nodes": sorted(reached),
    }


def optimize(s):
    base = assess(s)
    plans = []
    for bits in itertools.product([0, 1], repeat=6):
        chosen = [i for i, b in zip(INTERVENTIONS, bits) if b]
        ids = {i["id"] for i in chosen}
        cost = sum(i["cost"] for i in chosen)
        if cost > s.budget_usd or ids & set(s.rejected_interventions):
            continue
        if any(
            set(i["prerequisites"]) - ids or set(i["incompatibilities"]) & ids
            for i in chosen
        ):
            continue
        after = assess(s, chosen)
        unlocked = [
            u["id"]
            for b, u in zip(base["uses"], after["uses"])
            if b["status"] != "PASS" and u["status"] == "PASS"
        ]
        score = sum(
            s.use_weights.get(u["id"], u["weight"]) for u in USES if u["id"] in unlocked
        )
        plans.append(
            {
                "selected_interventions": chosen,
                "total_cost_usd": cost,
                "unlocked_uses": unlocked,
                "weighted_benefit": score,
                "feasibility_after": after,
            }
        )
    plans.sort(
        key=lambda p: (
            -p["weighted_benefit"],
            p["total_cost_usd"],
            len(p["selected_interventions"]),
            sorted(i["id"] for i in p["selected_interventions"]),
        )
    )
    result = {
        **plans[0],
        "runner_up": plans[1] if len(plans) > 1 else None,
        "feasibility_before": base,
        "portfolios_considered": 64,
        "eligible_portfolios": len(plans),
        "engine_version": VERSION,
        "data_mode": "fixture",
        "calculation_status": "complete",
        "source_refs": ["fixture-layout", "fixture-interventions"],
        "scenario": s.model_dump(),
        "run_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notice": "Preliminary modeled screening only. No regulatory authorization. All demonstration data and costs are synthetic.",
    }
    if s.building_id != "DEMO-HOU-001":
        from backend.realdata import context

        c = context()
        result.update(
            data_mode="cached_sponsor",
            source_refs=[
                "matterport-rooms",
                "vexcel-parcel",
                "scenario-assumptions",
                "matterport-geometry",
            ],
            evidence=c["evidence"]
            + [
                {
                    "evidence_id": "fixture-interventions",
                    "status": "estimated",
                    "observation": "Authored simulated intervention costs; not sourced construction quotations.",
                }
            ]
            + [
                {
                    "evidence_id": "scenario-assumptions",
                    "status": "approved_assumption",
                    "observation": s.assumptions,
                }
            ],
            building=c,
            notice="Preliminary screening on cached sponsor measurements. PASS is conditional on explicit scenario assumptions. Routes and permissions are not verified. Intervention costs are simulated.",
            reuse_proxy={
                "value": c["area_proxy_sqm"] if result["unlocked_uses"] else 0,
                "unit": "m² of candidate room area",
                "description": "Potential room reuse, counted once across uses; not carbon savings.",
            },
        )
    return result


def db():
    c = sqlite3.connect(ROOT / "data/scenarios.sqlite")
    c.execute(
        "CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, payload TEXT, decision TEXT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS decisions(run_id TEXT, decision TEXT, timestamp TEXT)"
    )
    return c


def save(p):
    with db() as c:
        c.execute(
            "INSERT INTO runs VALUES(?,?,?)", (p["run_id"], json.dumps(p), "pending")
        )
    return p


def getrun(id):
    with db() as c:
        r = c.execute("SELECT payload,decision FROM runs WHERE id=?", (id,)).fetchone()
    if not r:
        raise HTTPException(404, "Scenario not found")
    with db() as c:
        audit = [
            {"decision": row[0], "timestamp": row[1]}
            for row in c.execute(
                "SELECT decision,timestamp FROM decisions WHERE run_id=? ORDER BY rowid",
                (id,),
            )
        ]
    return {
        **json.loads(r[0]),
        "decision_history": audit,
        "decision": json.loads(r[1]) if r[1].startswith("{") else r[1],
    }


def building(id):
    from backend.realdata import context

    if id != BUILDING["building_id"] and (
        not context() or id != context()["building_id"]
    ):
        raise HTTPException(404, "Building not found")


@app.get("/api/health")
def health():
    from backend.realdata import context

    return {
        "status": "ok",
        "data_mode": "cached_sponsor" if context() else "fixture",
        "engine_version": VERSION,
        "sponsor_status": "cached_verified" if context() else "not_ingested",
        "llm_provider": "openai" if os.getenv("OPENAI_API_KEY") else "ollama",
        "llm_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.get("/api/buildings")
def buildings():
    from backend.realdata import context

    real = context()
    return ([real] if real else []) + [BUILDING]


@app.get("/api/buildings/{id}")
def detail(id: str):
    building(id)
    from backend.realdata import context

    return BUILDING if id == BUILDING["building_id"] else context()


@app.get("/api/config")
def config():
    return {
        "expression_operators": ["AND", "OR"],
        "uses": USES,
        "interventions": INTERVENTIONS,
    }


@app.post("/api/buildings/{id}/assess")
def assessment(id: str, s: Scenario):
    building(id)
    s.building_id = id
    return {
        "run_id": str(uuid.uuid4()),
        "engine_version": VERSION,
        "data_mode": "fixture" if id == BUILDING["building_id"] else "cached_sponsor",
        "source_refs": (
            ["fixture-layout"]
            if id == BUILDING["building_id"]
            else ["matterport-rooms", "vexcel-parcel", "matterport-geometry"]
        ),
        "calculation_status": "complete",
        **assess(s),
    }


@app.post("/api/buildings/{id}/optimize")
def optimization(id: str, s: Scenario):
    building(id)
    s.building_id = id
    return save(optimize(s))


@app.get("/api/scenarios")
def scenarios():
    with db() as c:
        return [
            json.loads(r[0])
            for r in c.execute("SELECT payload FROM runs ORDER BY rowid DESC LIMIT 50")
        ]


@app.get("/api/scenarios/{id}")
def scenario(id: str):
    return getrun(id)


class Compare(BaseModel):
    scenario_a: Scenario
    scenario_b: Scenario


@app.post("/api/scenarios/compare")
def compare(v: Compare):
    a, b = optimize(v.scenario_a), optimize(v.scenario_b)
    return {
        "before": a,
        "after": b,
        "cost_delta": b["total_cost_usd"] - a["total_cost_usd"],
        "new_uses": sorted(set(b["unlocked_uses"]) - set(a["unlocked_uses"])),
    }


@app.post("/api/scenarios/{id}/decision")
def decision(id: str, d: Decision):
    getrun(id)
    record = {
        "decision": d.decision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with db() as c:
        c.execute("UPDATE runs SET decision=? WHERE id=?", (json.dumps(record), id))
        c.execute(
            "INSERT INTO decisions VALUES(?,?,?)", (id, d.decision, record["timestamp"])
        )
    return record


@app.get("/api/reports/{id}")
def report(id: str, format: Literal["json", "markdown"] = "markdown"):
    p = getrun(id)
    if format == "json":
        return Response(
            json.dumps(p, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=spaceunlock.json"},
        )
    text = (
        f"# SpaceUnlock planning memo\n\n{p['notice']}\n\nRun: {id}\nEngine: {VERSION}\nData: {p['data_mode']}\n\nBudget: ${p['scenario']['budget_usd']:,.0f}\nEstimated spend: ${p['total_cost_usd']:,.0f}\nNew uses: {', '.join(p['unlocked_uses']) or 'None'}\n\n## Proposed interventions\n"
        + "\n".join(
            f"- {i['name']}: ${i['cost']} — {i['cost_basis']}"
            for i in p["selected_interventions"]
        )
        + "\n\n## Evidence and unresolved gates\n"
        + "\n".join(
            f"- {u['name']}: {u['status']}; {u['external_gate']}; checks: {json.dumps(u['checks'])}"
            for u in p["feasibility_after"]["uses"]
        )
        + "\n\n## Source register\n"
        + json.dumps(p.get("evidence", BUILDING["evidence"]), indent=2)
        + "\n\n## Scenario assumptions\n"
        + json.dumps(p["scenario"].get("assumptions", {}), indent=2)
        + "\n\nDecision: "
        + str(p["decision"])
    )
    return Response(
        text,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=spaceunlock.md"},
    )


@app.post("/api/agent/run")
async def agent(s: Scenario):
    p = optimize(s)
    verified = assess(s, p["selected_interventions"])
    assert verified == p["feasibility_after"]
    from backend.realdata import context

    property_context = (
        BUILDING if s.building_id == BUILDING["building_id"] else context()
    )
    p["trace"] = [
        {"tool": n, "result": r}
        for n, r in [
            ("get_property_context", property_context),
            ("assess_building", p["feasibility_before"]),
            (
                "optimize_plan",
                {"cost": p["total_cost_usd"], "unlocked": p["unlocked_uses"]},
            ),
            (
                "compare_scenarios",
                {"before": p["feasibility_before"], "after": verified},
            ),
            ("validate_plan", {"valid": True}),
            ("draft_proposal", {"approval": "awaiting explicit user action"}),
        ]
    ]
    p["agent_mode"] = "deterministic workflow"
    p["explanation"] = (
        f"Evaluated 64 portfolios. The recommendation unlocks {len(p['unlocked_uses'])} additional modeled uses for ${p['total_cost_usd']:,.0f}. Review unknown checks and external approvals before adopting this draft."
    )
    if any(
        word in s.request_text.lower()
        for word in [
            "certify",
            "certification",
            "legally approve",
            "approve construction",
            "ignore safety",
        ]
    ):
        p["explanation"] = (
            "I cannot certify compliance or authorize construction. This is preliminary screening only; external approvals remain unverified."
        )
        p["agent_mode"] = "safety response"
        return save(p)
    if True:
        try:
            from backend.llm_agent import run_agent
            from backend.realdata import context

            property_context = (
                BUILDING if s.building_id == BUILDING["building_id"] else context()
            )
            explanation, trace = await run_agent(
                s.model_dump(),
                {
                    "get_property_context": lambda: property_context,
                    "assess_building": lambda: assess(s),
                    "optimize_plan": lambda: optimize(s),
                    "compare_scenarios": lambda: {
                        "before": assess(s),
                        "after": assess(s, p["selected_interventions"]),
                    },
                    "draft_proposal": lambda: {
                        "selected": p["selected_interventions"],
                        "notice": p["notice"],
                        "approval": "pending explicit user action",
                    },
                },
            )
            p["explanation"] = explanation
            p["trace"] = trace + [
                {
                    "tool": "validate_plan",
                    "result": {
                        "valid": assess(s, p["selected_interventions"])
                        == p["feasibility_after"],
                        "budget_satisfied": p["total_cost_usd"] <= s.budget_usd,
                    },
                }
            ]
            p["agent_mode"] = (
                "OpenAI tool-calling agent"
                if os.getenv("OPENAI_API_KEY")
                else "Ollama local tool agent"
            )
        except Exception:
            p["llm_status"] = "unavailable; deterministic explanation used"
    return save(p)


@app.post("/api/scenarios/{id}/replay")
def replay(id: str):
    from backend.realdata import SNAPSHOT

    original = getrun(id)
    if original["engine_version"] != VERSION:
        raise HTTPException(409, "Replay requires the original engine version")
    token = SNAPSHOT.set(original.get("building"))
    try:
        current = optimize(Scenario(**original["scenario"]))
        keys = [
            "selected_interventions",
            "total_cost_usd",
            "unlocked_uses",
            "feasibility_before",
            "feasibility_after",
        ]
        return {
            "reproduced": all(current[k] == original[k] for k in keys),
            "engine_version": VERSION,
            "original_run_id": id,
            "result": current,
        }
    finally:
        SNAPSHOT.reset(token)


@app.post("/api/scenarios/frontier")
def frontier(s: Scenario):
    points = []
    for budget in [0, 2000, 4000, 5500, 7500, 9500, 12000, 15000, 20000, 30000]:
        candidate = s.model_copy(update={"budget_usd": budget})
        p = optimize(candidate)
        points.append(
            {
                "budget": budget,
                "cost": p["total_cost_usd"],
                "unlocked": len(p["unlocked_uses"]),
                "weighted_benefit": p["weighted_benefit"],
                "uses": p["unlocked_uses"],
            }
        )
    return {
        "points": points,
        "data_mode": (
            "fixture" if s.building_id == BUILDING["building_id"] else "cached_sponsor"
        ),
    }


from backend.connectors import router as integrations_router

app.include_router(integrations_router)
if (ROOT / "frontend/dist").exists():
    app.mount(
        "/", StaticFiles(directory=ROOT / "frontend/dist", html=True), name="frontend"
    )
