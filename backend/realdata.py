"""Real evidence normalization. No inferred circulation, permission or utility claims."""

import json
from collections import defaultdict
from functools import lru_cache
from contextvars import ContextVar

SNAPSHOT = ContextVar("spaceunlock_snapshot", default=None)
from pathlib import Path
from shapely.geometry import shape, Point
from fastapi import HTTPException
from backend.rules import all_checks, evaluate
import hashlib

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/private/real-building.json"
ASSUMPTIONS = {
    "arrival_path": "Continuous access from street to this scanned floor is available",
    "entrance_available": "An existing entrance can be activated with owner permission",
    "room_available": "The measured room can be reassigned",
    "route_passable": "An internal route exists and can be cleared without construction",
    "hours": "Operating hours have owner consent",
    "power": "Electricity is available",
    "pickup_permission": "Exterior pickup is allowed and operationally safe",
}


def sqm(value, units):
    if value is None:
        return None
    return (
        float(value) * 0.09290304
        if units == "imperial"
        else float(value) if units == "metric" else None
    )


def raw():
    return json.loads(PATH.read_text())


def topology(j):
    rooms = j.get("geometry", {}).get("rooms", [])
    edges_by_id = defaultdict(list)
    lines = []
    floors = {}
    nodes = []
    for r in rooms:
        f = r.get("floor") or {}
        floors[f.get("id", "unknown")] = f
        coords = []
        for e in (r.get("boundary") or {}).get("edges") or []:
            vertices = e.get("vertices") or []
            if len(vertices) >= 2:
                a, b = vertices[0]["position"], vertices[1]["position"]
                coords.extend([a, b])
                lines.append(
                    {
                        "room_id": r["id"],
                        "floor_id": f.get("id"),
                        "a": a,
                        "b": b,
                        "has_door": any(
                            o.get("type") in ["doorway", "divider"]
                            for o in e.get("openings") or []
                        ),
                    }
                )
            if any(
                o.get("type") in ["doorway", "divider"] for o in e.get("openings") or []
            ):
                edges_by_id[e["id"]].append(r["id"])
        if coords:
            nodes.append(
                {
                    "id": r["id"],
                    "floor_id": f.get("id"),
                    "x": sum(v["x"] for v in coords) / len(coords),
                    "y": sum(v["y"] for v in coords) / len(coords),
                }
            )
    edges = []
    candidates = []
    for id, rs in edges_by_id.items():
        rs = list(dict.fromkeys(rs))
        if len(rs) == 2:
            edges.append(
                {
                    "id": id,
                    "from": rs[0],
                    "to": rs[1],
                    "status": "observed_opening",
                    "evidence_ids": ["matterport-geometry"],
                }
            )
        elif len(rs) == 1:
            candidates.append(rs[0])
    return {
        "nodes": nodes,
        "edges": edges,
        "lines": lines,
        "floors": list(floors.values()),
        "entry_candidates": list(dict.fromkeys(candidates)),
    }


def context():
    if SNAPSHOT.get() is not None:
        return SNAPSHOT.get()
    if not PATH.exists():
        return None
    return _context(str(PATH), PATH.stat().st_mtime_ns)


@lru_cache(maxsize=4)
def _context(path, mtime):
    j = raw()
    topo = topology(j)
    m = j["matterport"]["data"]
    geo = m["geolocation"]
    point = Point(float(geo["long"]), float(geo["lat"]))
    parcels = []
    for f in j["vexcel"]["data"].get("features", []):
        try:
            if shape(f["geometry"]).covers(point):
                parcels.append(f)
        except (ValueError, TypeError, KeyError):
            continue
    parcels.sort(
        key=lambda f: f["properties"].get("metadata.ortho-date-estimate") or "",
        reverse=True,
    )
    parcel = parcels[0] if parcels else None
    rooms = []
    for r in m.get("rooms") or []:
        d = r.get("dimensions") or {}
        rooms.append(
            {
                "id": r["id"],
                "label": r.get("label") or "Unlabeled measured room",
                "area_sqm": sqm(d.get("areaFloor"), d.get("units")),
            }
        )
    rooms.sort(key=lambda r: r["area_sqm"] or 0, reverse=True)
    props = parcel["properties"] if parcel else {}
    hardscape = sqm(props.get("hardscapes.area"), "imperial")
    evidence = [
        {
            "evidence_id": "matterport-rooms",
            "status": "observed",
            "source_type": "Matterport",
            "source_ref": "https://my.matterport.com/show/?m=" + m["id"],
            "observation": "Measured room floor areas, converted from source units. Labels may be missing.",
            "value": rooms[0]["area_sqm"] if rooms else None,
        },
        {
            "evidence_id": "vexcel-parcel",
            "status": "observed" if parcel else "unknown",
            "source_type": "Vexcel",
            "source_ref": "https://api.vexcelgroup.com/v2/property/extract",
            "observation": "Latest returned parcel containing scan coordinates. Hardscape area is a screening proxy, not usable loading space.",
            "capture_date": props.get("metadata.ortho-date-estimate"),
            "value": hardscape,
        },
    ]
    evidence.append(
        {
            "evidence_id": "matterport-geometry",
            "status": "observed",
            "source_type": "Matterport",
            "source_ref": "https://my.matterport.com/show/?m=" + m["id"],
            "observation": "Shared wall boundaries with doorway/divider openings define candidate internal connections; passability is not established.",
        }
    )
    spaces = [
        {
            "id": r["id"],
            "label": r["label"],
            "area_sqm": r["area_sqm"],
            "x": 65 + (i % 5) * 115,
            "y": 65 + (i // 5) * 85,
        }
        for i, r in enumerate(rooms[:15])
    ]
    return {
        "building_id": "MP-" + m["id"],
        "name": m.get("name") or m["id"],
        "location": m["address"]["address"],
        "area_sqm": sqm(
            (m.get("dimensions") or {}).get("areaFloor"),
            (m.get("dimensions") or {}).get("units"),
        ),
        "rooms": rooms,
        "spaces": spaces,
        "graph": topo,
        "evidence": evidence,
        "data_revision": hashlib.sha256(PATH.read_bytes()).hexdigest()[:16],
        "data_mode": "cached_sponsor",
        "is_synthetic": False,
        "hardscape_sqm": hardscape,
        "geolocation": geo,
        "model_id": m["id"],
        "assumptions": ASSUMPTIONS,
        "parcel_match": bool(parcel),
        "capture_date": props.get("metadata.ortho-date-estimate"),
        "graph_status": "Observed shared doorway topology; passability and entrance function require confirmation",
        "area_proxy_sqm": rooms[0]["area_sqm"] if rooms else None,
        "target_room_id": rooms[0]["id"] if rooms else None,
    }


def assess(s, selected, uses):
    c = context()
    ass = s.assumptions
    ids = {i["id"] for i in selected}
    missing = set(s.withheld_sources)
    area = None if "matterport" in missing else c["area_proxy_sqm"]
    hard = None if "vexcel" in missing else c["hardscape_sqm"]
    # Operational interventions can only act on explicit assumptions, never invent facts.
    entrance = (
        True
        if bool(ids & {"alternate_entrance", "entrance_mod"})
        and ass.get("entrance_available") is True
        else None
    )
    route = None
    reached = set()
    active = []
    start = s.entry_room_id or next(
        (r for r in c["graph"]["entry_candidates"] if r == c["target_room_id"]), None
    )
    if start and start not in {r["id"] for r in c["rooms"]}:
        raise HTTPException(422, "Unknown entry room")
    if (
        entrance
        and ass.get("arrival_path") is True
        and ass.get("route_passable") is True
        and bool(ids & {"clear_hall", "signed_route", "entrance_mod"})
    ):
        if start:
            reached = {start}
            active = [e for e in c["graph"]["edges"] if e["id"] not in s.disabled_edges]
            for _ in c["rooms"]:
                for e in active:
                    if e["from"] in reached or e["to"] in reached:
                        reached.update([e["from"], e["to"]])
            route = c["target_room_id"] in reached
        else:
            route = None
    allocation = (
        True if "flex_room" in ids and ass.get("room_available") is True else None
    )
    pickup = True if "pickup" in ids and ass.get("pickup_permission") is True else None
    if "entrance_A_to_lobby" in s.disabled_edges:
        route = False

    def leaf(key, actual, required, source, provenance):
        state = (
            "UNKNOWN"
            if actual is None
            else (
                "PASS"
                if (
                    actual == required
                    if isinstance(required, bool)
                    else actual >= required
                )
                else "FAIL"
            )
        )
        return {
            "capability": key,
            "actual": actual,
            "required": required,
            "status": state,
            "source_refs": (
                [source, "matterport-geometry"]
                if key == "continuous_route"
                else [source]
            ),
            "provenance": provenance,
        }

    out = []
    for u in uses:
        threshold = u["minimum_area_sqm"]
        checks = [
            leaf("room_area_sqm", area, threshold, "matterport-rooms", "observed"),
            leaf(
                "allocated_room",
                ass.get("room_available") if u["id"] == "service" else allocation,
                True,
                "scenario-assumptions",
                "approved_assumption",
            ),
            leaf(
                "continuous_route",
                route,
                True,
                "scenario-assumptions",
                "approved_assumption",
            ),
        ]
        if u["id"] == "service":
            checks.append(
                leaf(
                    "operating_hours",
                    ass.get("hours"),
                    True,
                    "scenario-assumptions",
                    "approved_assumption",
                )
            )
        if u["id"] == "cowork":
            checks.append(
                leaf(
                    "electricity",
                    ass.get("power"),
                    True,
                    "scenario-assumptions",
                    "approved_assumption",
                )
            )
        if u["id"] == "distribution":
            checks.extend(
                [
                    leaf(
                        "exterior_hardscape_proxy_sqm",
                        hard,
                        20,
                        "vexcel-parcel",
                        "observed",
                    ),
                    leaf(
                        "pickup_permission",
                        pickup,
                        True,
                        "scenario-assumptions",
                        "approved_assumption",
                    ),
                ]
            )
        expression = u.get("real_requirement_expression") or {
            "op": "AND",
            "children": [{"check": i} for i in range(len(checks))],
        }
        status = evaluate(expression, checks)
        out.append(
            {
                **u,
                "status": status,
                "checks": checks,
                "requirement_expression": expression,
                "conditional": status == "PASS",
                "external_gate": u["gate"] + " — NOT VERIFIED",
            }
        )
    return {
        "uses": out,
        "active_edges": [e["id"] for e in active],
        "reachable_nodes": sorted(reached),
        "conditional_on_assumptions": True,
    }
