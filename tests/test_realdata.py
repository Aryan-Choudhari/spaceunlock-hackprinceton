import copy, time
import pytest
from backend import realdata
from backend.main import Scenario, optimize, assess


@pytest.fixture
def source(monkeypatch):
    # Authored fixture isolates engine tests from proprietary data and API availability.
    c = {
        "building_id": "MP-test",
        "name": "Test source",
        "area_proxy_sqm": 66,
        "hardscape_sqm": 4,
        "target_room_id": "room",
        "rooms": [{"id": "entry"}, {"id": "room"}],
        "evidence": [],
        "graph": {
            "entry_candidates": ["entry"],
            "edges": [{"id": "door", "from": "entry", "to": "room"}],
        },
    }
    monkeypatch.setattr(realdata, "context", lambda: c)
    return c


def scenario():
    return Scenario(
        building_id="MP-test",
        entry_room_id="entry",
        assumptions={k: True for k in realdata.ASSUMPTIONS},
    )


def test_both_sources_bind_decisions(source):
    s = scenario()
    p = optimize(s)
    assert "workshop" in p["unlocked_uses"]
    assert "distribution" not in p["unlocked_uses"]
    source["hardscape_sqm"] = 30
    assert "distribution" in optimize(s)["unlocked_uses"]
    source["area_proxy_sqm"] = 10
    assert not optimize(s)["unlocked_uses"]


def test_missing_source_becomes_unknown(source):
    s = scenario()
    s.withheld_sources = ["matterport"]
    p = optimize(s)
    assert not p["unlocked_uses"]
    assert p["data_mode"] == "cached_sponsor"


def test_unknowns_not_optimized_away(source):
    s = scenario()
    s.assumptions = {}
    assert not optimize(s)["unlocked_uses"]


def test_doorway_reachability_recomputed(source):
    s = scenario()
    assert optimize(s)["unlocked_uses"]
    s.disabled_edges = ["door"]
    assert not optimize(s)["unlocked_uses"]


def test_cost_and_counterfactual(source):
    s = scenario()
    s.budget_usd = 499
    assert optimize(s)["total_cost_usd"] == 0
    s.budget_usd = 15000
    p = optimize(s)
    assert p["total_cost_usd"] == 9500
    s.rejected_interventions = ["flex_room"]
    assert optimize(s)["unlocked_uses"] == ["service"]


def test_performance_and_reproducibility(source):
    s = scenario()
    start = time.perf_counter()
    runs = [optimize(s) for _ in range(10)]
    assert time.perf_counter() - start < 2
    assert all(
        r["selected_interventions"] == runs[0]["selected_interventions"] for r in runs
    )


def test_alternative_entrance_portfolio_after_rejection(source):
    s = scenario()
    s.rejected_interventions = ["alternate_entrance"]
    p = optimize(s)
    assert "entrance_mod" in {i["id"] for i in p["selected_interventions"]}
    assert p["total_cost_usd"] == 13000
    assert p["unlocked_uses"] == ["workshop", "service", "cowork"]
