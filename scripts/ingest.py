"""Fetch a matched property into the ignored private cache; never prints secrets."""

import argparse, asyncio, json, os
from datetime import datetime, timezone
from shapely.geometry import Point, shape
from backend.connectors import model, graph, property_data, Location, PRIVATE


async def ingest(id):
    m = await model(id)
    geo = m["data"].get("geolocation")
    if not geo:
        raise ValueError(
            "This model has no coordinates; cannot establish a Vexcel match"
        )
    lat, lon = float(geo["lat"]), float(geo["long"])
    v = await property_data(Location(latitude=lat, longitude=lon))
    if not any(
        shape(f["geometry"]).covers(Point(lon, lat))
        for f in v["data"].get("features", [])
    ):
        raise ValueError("No containing Vexcel parcel returned; keeping previous cache")
    g = await graph(
        "query($id:ID!){model(id:$id){rooms{id floor{id label sequence} boundary{edges{id type vertices{id position{x y}} openings{id type width}}}}}}",
        {"id": id},
    )
    record = {
        "matterport": m,
        "vexcel": v,
        "geometry": g["model"],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    PRIVATE.mkdir(parents=True, exist_ok=True)
    p = PRIVATE / "real-building.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, indent=2))
    tmp.chmod(0o600)
    os.replace(tmp, p)
    print(
        "Cached verified coordinate match:",
        id,
        "rooms:",
        len(m["data"].get("rooms", [])),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    args = parser.parse_args()
    asyncio.run(ingest(args.model_id))
