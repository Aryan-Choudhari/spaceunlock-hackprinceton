import { useEffect, useState } from "react";
async function request(path: string, body?: unknown) {
  const r = await fetch(
    "/api/integrations" + path,
    body
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {},
  );
  const v = await r.json();
  if (!r.ok)
    throw Error(typeof v.detail === "string" ? v.detail : "Request failed");
  return v;
}
export default function Connections() {
  const [status, S] = useState<any>(),
    [query, Q] = useState("Houston"),
    [results, R] = useState<any>(),
    [selected, M] = useState<any>(),
    [error, E] = useState(""),
    [busy, B] = useState(false),
    [exterior, V] = useState<any>();
  async function refresh() {
    const s = await request("/status");
    try {
      const p = await request("/agent/provider");
      s.agent = { status: p.provider + " " + p.status };
    } catch {}
    S(s);
    M(s.selected_model);
  }
  useEffect(() => {
    refresh().catch((e) => E(e.message));
  }, []);
  async function search(offset?: string) {
    B(true);
    E("");
    try {
      R(
        await request(
          "/matterport/models?query=" +
            encodeURIComponent(query) +
            (offset ? "&offset=" + encodeURIComponent(offset) : ""),
        ),
      );
      await refresh();
    } catch (e: any) {
      E(e.message);
    } finally {
      B(false);
    }
  }
  async function select(id: string) {
    B(true);
    E("");
    V(undefined);
    try {
      M(await request("/matterport/select", { model_id: id }));
      await refresh();
    } catch (e: any) {
      E(e.message);
    } finally {
      B(false);
    }
  }
  async function activate() {
    B(true);
    E("");
    try {
      await request("/matterport/activate", { model_id: selected.data.id });
      window.location.reload();
    } catch (e: any) {
      E(e.message);
    } finally {
      B(false);
    }
  }
  async function loadExterior() {
    B(true);
    E("");
    try {
      const geo = selected?.data?.geolocation;
      if (!geo)
        throw Error(
          "This model has no coordinates. Choose a model with a known location.",
        );
      V(
        await request("/vexcel/property", {
          latitude: Number(geo.lat),
          longitude: Number(geo.long),
        }),
      );
      await refresh();
    } catch (e: any) {
      E(e.message);
      await refresh();
    } finally {
      B(false);
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">SPONSOR CONNECTIONS</p>
      <h2>Explore real building evidence</h2>
      <p className="muted">
        Search your authorized Matterport models, select a scan, and retrieve
        Vexcel property evidence at the same coordinates. Activate a matched
        scan to use its room measurements, doorway topology and containing
        Vexcel parcel in the planner. Operating assumptions remain explicit.
      </p>
      <div className="connectionbadges">
        {["matterport", "vexcel", "agent"].map((k) => (
          <span className="pill" key={k}>
            {k.toUpperCase()}:{" "}
            {status?.[k]?.status?.replaceAll("_", " ") || "checking"}
          </span>
        ))}
      </div>
      <p className="small">
        SDK key:{" "}
        {status?.matterport?.sdk_configured
          ? "configured"
          : "optional · not configured"}
        . Model selection is saved locally; no manual model ID is required.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          search();
        }}
        className="connectionsearch"
      >
        <label>
          Model search
          <input
            value={query}
            onChange={(e) => Q(e.target.value)}
            placeholder="Houston, Los Angeles, or a property name"
          />
        </label>
        <button disabled={busy}>{busy ? "Working…" : "Search models"}</button>
      </form>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {results && (
        <>
          <p>{results.totalResults.toLocaleString()} matching models</p>
          <div className="modelresults">
            {results.results.map((m: any) => (
              <button
                className="history"
                disabled={busy}
                key={m.id}
                onClick={() => select(m.id)}
              >
                <b>{m.name || m.id}</b>
                <span>
                  {m.address?.address ||
                    m.address?.locality ||
                    "Address unavailable"}
                </span>
              </button>
            ))}
          </div>
          {results.nextOffset && (
            <button disabled={busy} onClick={() => search(results.nextOffset)}>
              Next page
            </button>
          )}
        </>
      )}
      {selected && (
        <div className="selectedmodel">
          <h3>{selected.data.name || selected.data.id}</h3>
          <p>
            {selected.data.address?.address} · Model {selected.data.id}
          </p>
          <p className="small">
            Observed through Matterport · {selected.data.rooms?.length ?? 0}{" "}
            rooms · Floor area:{" "}
            {selected.data.dimensions?.areaFloor ?? "unknown"}{" "}
            {selected.data.dimensions?.units || ""} (squared)
          </p>
          <a
            href={
              "https://my.matterport.com/show/?m=" +
              encodeURIComponent(selected.data.id)
            }
            target="_blank"
            rel="noreferrer"
          >
            Open authorized Matterport tour ↗
          </a>
          <p className="small">
            Tour access follows the model’s sharing settings. An SDK key is not
            required for this link.
          </p>
          <button
            disabled={busy || !selected.data.geolocation}
            onClick={activate}
          >
            Use matched property in planner
          </button>{" "}
          <button
            disabled={busy || !selected.data.geolocation}
            onClick={loadExterior}
          >
            Load Vexcel evidence at this location
          </button>
          <details>
            <summary>Room measurements and source record</summary>
            <pre>{JSON.stringify(selected, null, 2)}</pre>
          </details>
          {exterior && (
            <details open>
              <summary>
                Vexcel property evidence · {exterior.data.features?.length ?? 0}{" "}
                features
              </summary>
              <p>{exterior.planning_status}</p>
              <pre>{JSON.stringify(exterior.data, null, 2)}</pre>
            </details>
          )}
        </div>
      )}
    </section>
  );
}
