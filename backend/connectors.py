"""Read-only sponsor connections. Credentials never leave the backend."""

import json, os, re
from pathlib import Path
from datetime import datetime, timezone
import httpx
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "data/private"
router = APIRouter(prefix="/api/integrations")
STATE = {}


def config():
    return {**dotenv_values(ROOT / ".env"), **os.environ}


def selection():
    p = PRIVATE / "selected-model.json"
    return json.loads(p.read_text()) if p.exists() else None


async def graph(query, variables=None):
    env = config()
    key, token = env.get("MATTERPORT_API_KEY"), env.get("MATTERPORT_API_TOKEN")
    if not key or not token:
        raise HTTPException(503, "Matterport API key and token are required")
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.matterport.com/api/models/graph",
                auth=(key, token),
                json={"query": query, "variables": variables or {}},
            )
        if r.status_code != 200:
            raise HTTPException(502, f"Matterport returned HTTP {r.status_code}")
        payload = r.json()
        if payload.get("errors"):
            raise HTTPException(
                502, "Matterport rejected the query or denied access to this model"
            )
        STATE["matterport"] = {
            "status": "connected",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        return payload["data"]
    except httpx.HTTPError:
        raise HTTPException(502, "Matterport is unreachable; retry later")


@router.get("/status")
def status():
    env = config()
    return {
        "matterport": {
            **STATE.get(
                "matterport",
                {
                    "status": (
                        "configured"
                        if env.get("MATTERPORT_API_KEY")
                        and env.get("MATTERPORT_API_TOKEN")
                        else "missing_credentials"
                    )
                },
            ),
            "sdk_configured": bool(env.get("MATTERPORT_SDK_KEY")),
        },
        "vexcel": STATE.get(
            "vexcel",
            {
                "status": (
                    "configured" if env.get("VEXCEL_API_KEY") else "missing_credentials"
                )
            },
        ),
        "agent": {
            "status": (
                "configured" if env.get("OPENAI_API_KEY") else "deterministic_fallback"
            )
        },
        "selected_model": selection(),
        "planner_data_mode": (
            "cached_sponsor" if (PRIVATE / "real-building.json").exists() else "fixture"
        ),
    }


@router.get("/matterport/models")
async def models(
    query: str = Query(default="", max_length=200), offset: str | None = None
):
    return (
        await graph(
            "query($query:String,$offset:String){models(query:$query,offset:$offset,pageSize:20){totalResults nextOffset results{id name address{address locality administrativeArea} geolocation{lat long}}}}",
            {"query": query or None, "offset": offset},
        )
    )["models"]


@router.get("/matterport/models/{model_id}")
async def model(model_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", model_id):
        raise HTTPException(422, "Invalid model ID")
    data = await graph(
        "query($id:ID!){model(id:$id){id name address{address locality administrativeArea} geolocation{lat long} rooms{id label dimensions{areaFloor units}} dimensions{areaFloor units}}}",
        {"id": model_id},
    )
    if not data.get("model"):
        raise HTTPException(404, "Model not found")
    return {
        "source": "Matterport Model API",
        "status": "observed",
        "data": data["model"],
        "planning_status": "Needs matching property evidence and route annotations before feasibility assessment",
    }


class Select(BaseModel):
    model_id: str = Field(min_length=1, max_length=100)


@router.post("/matterport/select")
async def select(body: Select):
    result = await model(body.model_id)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    path = PRIVATE / "selected-model.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, indent=2))
    temp.replace(path)
    path.chmod(0o600)
    return result


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


@router.post("/vexcel/property")
async def property_data(loc: Location):
    key = config().get("VEXCEL_API_KEY")
    if not key:
        raise HTTPException(503, "Vexcel API key is required")
    try:
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.get(
                "https://api.vexcelgroup.com/v2/property/extract",
                headers={"X-API-KEY": key},
                params={
                    "wkt": f"POINT({loc.longitude} {loc.latitude})",
                    "srid": 4326,
                    "layer": "urban,urban-r,wide-area,urban-g",
                    "latest": "true",
                    "include": "precomputed",
                    "unit-system": "imperial",
                },
            )
        STATE["vexcel"] = {
            "status": (
                "connected"
                if r.status_code == 200
                else (
                    "no_coverage"
                    if r.status_code == 404
                    else (
                        "authentication_failed"
                        if r.status_code in (401, 403)
                        else "source_unavailable"
                    )
                )
            ),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        if r.status_code != 200:
            raise HTTPException(
                502,
                f"Vexcel returned HTTP {r.status_code}; "
                + (
                    "no property coverage at this location"
                    if r.status_code == 404
                    else "check access or retry later"
                ),
            )
        return {
            "source": "Vexcel property/extract",
            "status": "observed",
            "coordinates": loc.model_dump(),
            "units": "imperial",
            "data": r.json(),
            "planning_status": "Exterior attributes do not establish passable routes or operating permission",
        }
    except httpx.HTTPError:
        raise HTTPException(502, "Vexcel is unreachable; retry later")


@router.get("/vexcel/imagery")
async def imagery():
    from backend.realdata import context
    from fastapi.responses import Response
    import math

    c = context()
    if not c:
        raise HTTPException(404, "No matched property selected")
    PRIVATE.mkdir(parents=True, exist_ok=True)
    cache = PRIVATE / ("aerial-" + c["model_id"] + ".jpg")
    if cache.exists():
        return Response(
            cache.read_bytes(),
            media_type="image/jpeg",
            headers={"Cache-Control": "private, max-age=3600"},
        )
    key = config().get("VEXCEL_API_KEY")
    if not key:
        raise HTTPException(503, "Vexcel credentials missing")
    lat, lon = float(c["geolocation"]["lat"]), float(c["geolocation"]["long"])
    dy = 60 / 111320
    dx = 60 / (111320 * math.cos(math.radians(lat)))
    wkt = f"POLYGON(({lon-dx} {lat-dy},{lon+dx} {lat-dy},{lon+dx} {lat+dy},{lon-dx} {lat+dy},{lon-dx} {lat-dy}))"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://api.vexcelgroup.com/v2/ortho/extract",
                headers={"X-API-KEY": key},
                json={
                    "wkt": wkt,
                    "srid": 4326,
                    "layer": "urban,urban-r,wide-area,urban-g",
                    "crop": "bounding_box",
                    "image-format": "jpeg",
                },
            )
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith(
            "image/"
        ):
            raise HTTPException(502, "Aerial imagery unavailable")
        cache.write_bytes(r.content)
        cache.chmod(0o600)
        return Response(r.content, media_type="image/jpeg")
    except httpx.HTTPError:
        raise HTTPException(502, "Aerial request timed out")


@router.get("/agent/provider")
async def provider():
    if config().get("OPENAI_API_KEY"):
        return {"provider": "openai", "status": "configured"}
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/tags"
            )
        r.raise_for_status()
        names = [m["name"] for m in r.json().get("models", [])]
        chosen = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        return {
            "provider": "ollama",
            "status": "available" if chosen in names else "model_missing",
            "model": chosen,
            "models": names,
        }
    except (httpx.HTTPError, ValueError):
        return {"provider": "deterministic", "status": "ollama_unavailable"}


@router.post("/matterport/activate")
async def activate(body: Select):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", body.model_id):
        raise HTTPException(422, "Invalid model ID")
    from scripts.ingest import ingest
    from backend.realdata import context

    try:
        await ingest(body.model_id)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return context()
