from fastapi.testclient import TestClient
from backend import main
import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "ROOT", tmp_path)
    (tmp_path / "data").mkdir()
    return TestClient(main.app)


def test_reports_and_decision_audit(client):
    p = client.post(
        "/api/buildings/DEMO-HOU-001/optimize", json={"budget_usd": 15000}
    ).json()
    id = p["run_id"]
    for decision in ["approved_draft", "revise"]:
        assert (
            client.post(
                f"/api/scenarios/{id}/decision", json={"decision": decision}
            ).status_code
            == 200
        )
    saved = client.get(f"/api/scenarios/{id}").json()
    assert len(saved["decision_history"]) == 2
    for format in ["json", "markdown"]:
        assert client.get(f"/api/reports/{id}?format={format}").status_code == 200


def test_invalid_inputs(client):
    for body in [
        {"budget_usd": -1},
        {"disabled_edges": ["imaginary"]},
        {"use_weights": {"fake": 4}},
        {"rejected_interventions": ["fake"]},
    ]:
        assert (
            client.post("/api/buildings/DEMO-HOU-001/optimize", json=body).status_code
            == 422
        )
    assert client.get("/api/buildings/missing").status_code == 404
    assert (
        client.post(
            "/api/scenarios/missing/decision", json={"decision": "approved_draft"}
        ).status_code
        == 404
    )


def test_certification_request_denied(client):
    r = client.post(
        "/api/agent/run",
        json={"request_text": "Certify this property for legal occupancy"},
    )
    assert r.status_code == 200
    assert r.json()["agent_mode"] == "safety response"
    assert "cannot certify" in r.json()["explanation"]


def test_budget_frontier(client):
    r = client.post("/api/scenarios/frontier", json={"budget_usd": 15000})
    assert r.status_code == 200
    points = r.json()["points"]
    assert len(points) == 10
    assert all(p["cost"] <= p["budget"] for p in points)


def test_offline_provider_preserves_planner(client, monkeypatch):
    from backend import llm_agent

    async def unavailable(*args, **kwargs):
        raise ConnectionError("offline")

    monkeypatch.setattr(llm_agent, "run_agent", unavailable)
    r = client.post("/api/agent/run", json={"budget_usd": 15000})
    assert r.status_code == 200
    p = r.json()
    assert p["agent_mode"] == "deterministic workflow"
    assert "unavailable" in p["llm_status"]
    assert any(u["status"] == "UNKNOWN" for u in p["feasibility_after"]["uses"])


def test_absent_private_cache_loads_fixture(client, monkeypatch):
    from backend import realdata

    monkeypatch.setattr(realdata, "context", lambda: None)
    data = client.get("/api/buildings").json()
    assert len(data) == 1 and data[0]["is_synthetic"]
    assert (
        client.post("/api/buildings/DEMO-HOU-001/optimize", json={}).status_code == 200
    )


def test_saved_plan_replays(client):
    p = client.post(
        "/api/buildings/DEMO-HOU-001/optimize", json={"budget_usd": 15000}
    ).json()
    r = client.post("/api/scenarios/" + p["run_id"] + "/replay", json={})
    assert r.status_code == 200
    assert r.json()["reproduced"] is True
