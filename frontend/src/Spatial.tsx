import { useState } from "react";
export default function Spatial({
  building,
  disabled,
  onToggle,
}: {
  building: any;
  disabled: string[];
  onToggle: (id: string) => void;
}) {
  const [tour, Tour] = useState(false);
  const g = building.graph,
    [floor, F] = useState(
      g.floors?.find((f: any) => f.sequence === 0)?.id || g.floors?.[0]?.id,
    ),
    [hover, H] = useState("");
  const lines = g.lines.filter((l: any) => l.floor_id === floor),
    nodes = g.nodes.filter((n: any) => n.floor_id === floor);
  const points = lines.flatMap((l: any) => [l.a, l.b]);
  if (!points.length) return <p>No floor geometry available.</p>;
  const xs = points.map((p: any) => p.x),
    ys = points.map((p: any) => p.y),
    x = Math.min(...xs),
    y = Math.min(...ys),
    w = Math.max(...xs) - x,
    h = Math.max(...ys) - y,
    scale = Math.min(540 / (w || 1), 300 / (h || 1)),
    px = (v: number) => 40 + (v - x) * scale,
    py = (v: number) => 35 + (v - y) * scale;
  const room = building.rooms.find((r: any) => r.id === hover);
  return (
    <div>
      <div className="floorbuttons">
        <button
          onClick={() => Tour(false)}
          className={!tour ? "activefloor" : ""}
        >
          Floor plan
        </button>
        <button
          onClick={() => Tour(true)}
          className={tour ? "activefloor" : ""}
        >
          3D interior tour
        </button>
      </div>
      {tour ? (
        <div>
          <iframe
            title="Matterport interior walkthrough"
            src={
              "https://my.matterport.com/show/?m=" +
              encodeURIComponent(building.model_id) +
              "&play=1"
            }
            allow="fullscreen; xr-spatial-tracking"
            allowFullScreen
            style={{
              width: "100%",
              height: 420,
              border: 0,
              borderRadius: 8,
              marginTop: 15,
            }}
          />
          <p className="small">
            Tour access follows Matterport sharing permissions.{" "}
            <a
              href={"https://my.matterport.com/show/?m=" + building.model_id}
              target="_blank"
              rel="noreferrer"
            >
              Open separately ↗
            </a>
          </p>
        </div>
      ) : (
        <>
          <div className="floorbuttons">
            {g.floors
              .sort((a: any, b: any) => a.sequence - b.sequence)
              .map((f: any) => (
                <button
                  key={f.id}
                  className={f.id === floor ? "activefloor" : ""}
                  onClick={() => F(f.id)}
                >
                  {f.label || "Floor " + (f.sequence + 1)}
                </button>
              ))}
          </div>
          <svg
            viewBox="0 0 620 370"
            role="img"
            aria-label="Matterport measured floor boundaries"
          >
            <rect width="620" height="370" rx="8" fill="#f4f6ef" />
            {lines.map((l: any, i: number) => (
              <line
                key={i}
                x1={px(l.a.x)}
                y1={py(l.a.y)}
                x2={px(l.b.x)}
                y2={py(l.b.y)}
                stroke={
                  l.room_id === hover
                    ? "#c89538"
                    : l.has_door
                      ? "#85b88d"
                      : "#365744"
                }
                strokeWidth={l.room_id === hover ? 4 : l.has_door ? 1.5 : 2}
              />
            ))}
            {nodes.map((n: any) => {
              const r = building.rooms.find((r: any) => r.id === n.id);
              return (
                <g
                  key={n.id}
                  onMouseEnter={() => H(n.id)}
                  onFocus={() => H(n.id)}
                  tabIndex={0}
                  role="button"
                  aria-label={
                    "Room " +
                    Number(r?.area_sqm || 0).toFixed(1) +
                    " square meters"
                  }
                >
                  <circle
                    cx={px(n.x)}
                    cy={py(n.y)}
                    r={n.id === building.target_room_id ? 9 : 4}
                    fill={
                      n.id === building.target_room_id ? "#d2a84c" : "#52745b"
                    }
                  />
                  <title>
                    {r?.label}: {Number(r?.area_sqm || 0).toFixed(1)} m²
                  </title>
                </g>
              );
            })}
          </svg>
          <p className="small">
            {room
              ? `${room.label}: ${Number(room.area_sqm || 0).toFixed(1)} m²`
              : "Hover or focus a room to inspect measured area. Gold marks the candidate room."}
          </p>
          <p className="small muted">
            Matterport wall geometry · {g.nodes.length} rooms · {g.edges.length}{" "}
            shared doorway connections. Doorways do not establish accessible or
            legally permitted routes.
          </p>
          <details>
            <summary>Block a measured doorway connection</summary>
            {g.edges
              .filter((e: any) => nodes.some((n: any) => n.id === e.from))
              .map((e: any, i: number) => (
                <label key={e.id}>
                  <input
                    type="checkbox"
                    checked={disabled.includes(e.id)}
                    onChange={() => onToggle(e.id)}
                  />
                  Doorway {i + 1} · {e.id.slice(0, 8)}
                </label>
              ))}
          </details>
        </>
      )}
    </div>
  );
}
