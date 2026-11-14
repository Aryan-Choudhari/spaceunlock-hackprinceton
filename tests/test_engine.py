import pytest
from fastapi import HTTPException
from backend.main import Scenario, assess, optimize, INTERVENTIONS


def test_baseline_has_all_states():
    assert {u["status"] for u in assess(Scenario())["uses"]} == {
        "PASS",
        "FAIL",
        "UNKNOWN",
    }


def test_budget_and_reproducibility():
    for budget in [0, 499, 2000, 6000, 15000]:
        a, b = optimize(Scenario(budget_usd=budget)), optimize(
            Scenario(budget_usd=budget)
        )
        assert a["total_cost_usd"] <= budget
        assert a["selected_interventions"] == b["selected_interventions"]
        assert a["feasibility_after"] == b["feasibility_after"]


def test_critical_route_recomputed():
    s = Scenario(
        disabled_edges=[
            "street_to_entrance_A",
            "street_to_entrance_B",
            "street_to_loading",
        ]
    )
    assert all(u["status"] == "FAIL" for u in optimize(s)["feasibility_after"]["uses"])


def test_unknown_not_optimized_away():
    assert (
        next(
            u
            for u in optimize(Scenario())["feasibility_after"]["uses"]
            if u["id"] == "cowork"
        )["status"]
        == "UNKNOWN"
    )


def test_rejection_excludes_top_choice():
    p = optimize(Scenario())
    selected = p["selected_interventions"][0]["id"]
    q = optimize(Scenario(rejected_interventions=[selected]))
    assert selected not in [i["id"] for i in q["selected_interventions"]]


def test_invalid_graph_edge():
    with pytest.raises(HTTPException):
        optimize(Scenario(disabled_edges=["invented"]))


def test_prerequisites_and_exclusions():
    p = optimize(Scenario(budget_usd=100000))
    ids = {i["id"] for i in p["selected_interventions"]}
    for i in p["selected_interventions"]:
        assert set(i["prerequisites"]) <= ids
        assert not set(i["incompatibilities"]) & ids


def test_and_or_three_state_logic():
    from backend.rules import evaluate

    checks = [{"status": "UNKNOWN"}, {"status": "PASS"}, {"status": "FAIL"}]
    assert (
        evaluate({"op": "OR", "children": [{"check": 0}, {"check": 1}]}, checks)
        == "PASS"
    )
    assert (
        evaluate({"op": "AND", "children": [{"check": 0}, {"check": 1}]}, checks)
        == "UNKNOWN"
    )
    assert (
        evaluate(
            {
                "op": "AND",
                "children": [
                    {"op": "OR", "children": [{"check": 0}, {"check": 1}]},
                    {"check": 2},
                ],
            },
            checks,
        )
        == "FAIL"
    )
