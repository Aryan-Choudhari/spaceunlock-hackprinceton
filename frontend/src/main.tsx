import Frontier from "./Frontier";
import Spatial from "./Spatial";
import Connections from "./Connections";
import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowUpRight,
  Layers,
  Building2,
  SlidersHorizontal,
  Sparkles,
  Download,
  Check,
  History,
} from "lucide-react";
import "./style.css";
async function api(path: string, body?: unknown) {
  let r = await fetch(
    "/api" + path,
    body
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {},
  );
  if (!r.ok) throw Error(await r.text());
  return r.json();
}
function App() {
  const runSequence = useRef(0);
  const [replayMessage, ReplayMessage] = useState(""),
    [requestText, RequestText] = useState(""),
    [entry, Entry] = useState<string | undefined>(),
    [available, Available] = useState<any[]>([]),
    [assumptions, Assumptions] = useState<Record<string, boolean>>({}),
    [withheld, Withheld] = useState<string[]>([]),
    [b, B] = useState<any>(),
    [cfg, C] = useState<any>(),
    [p, P] = useState<any>(),
    [budget, S] = useState(15000),
    [disabled, D] = useState<string[]>([]),
    [reject, R] = useState<string[]>([]),
    [weights, W] = useState<any>({}),
    [busy, Q] = useState(false),
    [error, E] = useState(""),
    [tab, T] = useState("Planner"),
    [history, H] = useState<any[]>([]),
    [name, N] = useState("Community possibilities"),
    [decision, A] = useState(""),
    [old, O] = useState<any>(),
    [focus, F] = useState("");
  useEffect(() => {
    Promise.all([api("/buildings"), api("/config")])
      .then(([bs, c]) => {
        Available(bs);
        B(bs[0]);
        Entry(bs[0].target_room_id);
        C(c);
      })
      .catch((e) => E(e.message));
  }, []);
  const scenario = {
    request_text: requestText,
    building_id: b?.building_id,
    entry_room_id: entry,
    assumptions,
    withheld_sources: withheld,
    budget_usd: budget,
    disabled_edges: disabled,
    rejected_interventions: reject,
    use_weights: weights,
    name,
  };
  const dirty =
    p &&
    (p.scenario.budget_usd !== budget ||
      p.scenario.name !== name ||
      JSON.stringify(p.scenario.assumptions || {}) !==
        JSON.stringify(assumptions) ||
      JSON.stringify(p.scenario.disabled_edges) !== JSON.stringify(disabled) ||
      JSON.stringify(p.scenario.rejected_interventions) !==
        JSON.stringify(reject) ||
      JSON.stringify(p.scenario.use_weights) !== JSON.stringify(weights) ||
      JSON.stringify(p.scenario.withheld_sources || []) !==
        JSON.stringify(withheld) ||
      (p.scenario.entry_room_id ?? null) !== (entry ?? null));
  async function run() {
    const sequence = ++runSequence.current;
    Q(true);
    E("");
    try {
      const result = await api("/agent/run", scenario);
      if (sequence !== runSequence.current) return;
      O(p);
      P(result);
      A("");
      ReplayMessage("");
    } catch (e: any) {
      if (sequence === runSequence.current) E(e.message);
    } finally {
      if (sequence === runSequence.current) Q(false);
    }
  }
  useEffect(() => {
    if (b) run();
  }, [b]);
  const toggle = (a: string[], v: string) =>
    a.includes(v) ? a.filter((x) => x !== v) : [...a, v];
  return (
    <div className="app">
      <a className="skiplink" href="#main-content">
        Skip to planner
      </a>
      <aside>
        <div className="brand">
          <Layers /> space<span>unlock</span>
        </div>
        <div className="workspace">
          WORKSPACE <small>HackPrinceton / 2026</small>
        </div>
        {["Planner", "Evidence", "Agent trace", "Saved scenarios"].map(
          (x, i) => (
            <button
              className={"nav " + (tab === x ? "selected" : "")}
              onClick={() => {
                T(x);
                if (i === 3) api("/scenarios").then(H);
              }}
              key={x}
            >
              {
                [
                  <SlidersHorizontal />,
                  <Building2 />,
                  <Sparkles />,
                  <History />,
                ][i]
              }
              {x}
            </button>
          ),
        )}
        <div className="asidebottom">
          <span className="dot" /> Local workspace
          <small>Engine v1.0 · Source-aware planning</small>
        </div>
      </aside>
      <main id="main-content">
        <header>
          <span>PROPERTY INTELLIGENCE / ADAPTIVE REUSE</span>
          <span className="pill">
            ● {b?.is_synthetic ? "FIXTURE MODE" : "CACHED SPONSOR EVIDENCE"}
          </span>
        </header>
        <div className="title">
          <div>
            <p className="eyebrow">SMALL CHANGES. MORE POSSIBILITIES.</p>
            <h1>Make room for what’s next.</h1>
            <p className="muted">
              Discover what this building could become, within your budget.
            </p>
          </div>
          <span className="project">
            01 / HOUSTON <ArrowUpRight />
          </span>
        </div>
        {error && (
          <div role="alert" className="error">
            {error}
          </div>
        )}
        {!b ? (
          <p>Loading workspace…</p>
        ) : (
          <>
            <label>
              Property
              <select
                value={b.building_id}
                onChange={(e) => {
                  B(available.find((x) => x.building_id === e.target.value));
                  Entry(
                    available.find((x) => x.building_id === e.target.value)
                      ?.target_room_id,
                  );
                  P(undefined);
                  O(undefined);
                  Assumptions({});
                  Withheld([]);
                  D([]);
                }}
              >
                {available.map((x) => (
                  <option key={x.building_id} value={x.building_id}>
                    {x.name} ·{" "}
                    {x.is_synthetic ? "synthetic demo" : "real sponsor data"}
                  </option>
                ))}
              </select>
            </label>
            <section className="property">
              <div className="buildingicon">
                <Building2 size={30} />
              </div>
              <div>
                <h2>{b.name}</h2>
                <span className="muted">
                  {b.location} · {Math.round(b.area_sqm || 0)} m² · Reuse
                  screening
                </span>
              </div>
              <span className="pill">
                {b.is_synthetic ? "SYNTHETIC DATA" : "MATTERPORT + VEXCEL"}
              </span>
            </section>
            {tab === "Planner" && (
              <>
                <div className="columns">
                  <section className="panel map">
                    <div className="panelhead">
                      <div>
                        <p className="eyebrow">01 / SPATIAL CONTEXT</p>
                        <h2>
                          {b.is_synthetic
                            ? "A connected view of possibility"
                            : "Measured rooms, unexplored possibilities"}
                        </h2>
                      </div>
                      <span className="pill">
                        {p ? "OPTIMIZED" : "BASELINE"}
                      </span>
                    </div>
                    {!b.is_synthetic ? (
                      <Spatial
                        building={b}
                        disabled={disabled}
                        onToggle={(id) => D(toggle(disabled, id))}
                      />
                    ) : (
                      <svg
                        viewBox="0 0 620 370"
                        role="img"
                        aria-label="Interactive building connectivity map"
                      >
                        <defs>
                          <pattern
                            id="grid"
                            width="20"
                            height="20"
                            patternUnits="userSpaceOnUse"
                          >
                            <circle cx="1" cy="1" r="1" fill="#d8ded9" />
                          </pattern>
                        </defs>
                        <rect width="620" height="370" fill="url(#grid)" />
                        <rect
                          x="205"
                          y="30"
                          width="395"
                          height="305"
                          rx="8"
                          fill="#e6ece6"
                          stroke="#ccd4cd"
                        />
                        {b.graph.edges.map((e: any) => {
                          let a = b.spaces.find((n: any) => n.id === e.from),
                            z = b.spaces.find((n: any) => n.id === e.to),
                            active = p?.feasibility_after.active_edges.includes(
                              e.id,
                            );
                          return (
                            <g
                              key={e.id}
                              onClick={() => D(toggle(disabled, e.id))}
                            >
                              <line
                                x1={a.x}
                                y1={a.y}
                                x2={z.x}
                                y2={z.y}
                                stroke={
                                  disabled.includes(e.id)
                                    ? "#c56655"
                                    : active
                                      ? "#34745a"
                                      : "#abb7af"
                                }
                                strokeWidth="5"
                                strokeDasharray={active ? "" : "7 6"}
                              />
                              <title>
                                {e.id} — use controls below to block
                              </title>
                            </g>
                          );
                        })}
                        {b.spaces.map((n: any) => (
                          <g key={n.id}>
                            <circle
                              cx={n.x}
                              cy={n.y}
                              r="14"
                              fill={focus.includes(n.id) ? "#dca44d" : "#fff"}
                              stroke="#34745a"
                              strokeWidth="3"
                            />
                            <text
                              x={n.x}
                              y={n.y + 31}
                              textAnchor="middle"
                              fontSize="12"
                              fill="#334a40"
                            >
                              {n.label
                                ? n.label === "Unlabeled measured room"
                                  ? Math.round(n.area_sqm || 0) + " m²"
                                  : n.label
                                : n.id.replaceAll("_", " ")}
                            </text>
                          </g>
                        ))}
                      </svg>
                    )}
                    <div className="mapfooter">
                      {b.is_synthetic ? (
                        <>
                          <span>
                            <i /> Passable route
                          </span>
                          <span>− − Unavailable route</span>
                        </>
                      ) : (
                        <>
                          <span>
                            <i /> Measured boundaries
                          </span>
                          <span>Openings require review</span>
                        </>
                      )}
                      <span>
                        {b.is_synthetic
                          ? "Manual topology · not to scale"
                          : "Measured room boundaries"}
                      </span>
                    </div>
                    {!b.is_synthetic && (
                      <p className="small muted">
                        Largest measured room: {b.area_proxy_sqm?.toFixed(1)}{" "}
                        m².
                      </p>
                    )}
                    <details>
                      <summary>Simulate a blocked route</summary>
                      <div className="edgecontrols">
                        {!b.is_synthetic && (
                          <label>
                            <input
                              type="checkbox"
                              checked={disabled.includes("entrance_A_to_lobby")}
                              onChange={() =>
                                D(toggle(disabled, "entrance_A_to_lobby"))
                              }
                            />
                            Counterfactual: proposed access route unavailable
                          </label>
                        )}
                        {(b.is_synthetic ? b.graph.edges : []).map((e: any) => (
                          <label key={e.id}>
                            <input
                              type="checkbox"
                              checked={disabled.includes(e.id)}
                              onChange={() => D(toggle(disabled, e.id))}
                            />
                            {e.id.replaceAll("_", " ")}
                          </label>
                        ))}
                      </div>
                    </details>
                  </section>
                  <section className="panel controls">
                    <p className="eyebrow">02 / YOUR CONSTRAINTS</p>
                    <h2>Define the opportunity</h2>
                    <label>
                      Planning request (optional)
                      <input
                        value={requestText}
                        onChange={(e) => RequestText(e.target.value)}
                        placeholder="Explain the trade-offs for this scenario"
                        maxLength={1000}
                      />
                    </label>
                    <label>
                      Scenario name
                      <input value={name} onChange={(e) => N(e.target.value)} />
                    </label>
                    <label>
                      Intervention budget{" "}
                      <strong>${budget.toLocaleString()}</strong>
                      <input
                        type="range"
                        min="0"
                        max="30000"
                        step="500"
                        value={budget}
                        onChange={(e) => S(+e.target.value)}
                      />
                      <input
                        aria-label="Budget amount"
                        type="number"
                        min="0"
                        max="10000000"
                        value={budget}
                        onChange={(e) => S(+e.target.value)}
                      />
                    </label>
                    {!b.is_synthetic && (
                      <details open>
                        <summary>Explicit scenario assumptions</summary>
                        <label>
                          Proposed entrance room
                          <select
                            value={entry || b.target_room_id}
                            onChange={(e) => Entry(e.target.value)}
                          >
                            {b.graph.entry_candidates.map((id: string) => {
                              const r = b.rooms.find((r: any) => r.id === id);
                              return (
                                <option value={id} key={id}>
                                  {id === b.target_room_id
                                    ? "Candidate room"
                                    : "Room"}{" "}
                                  · {r?.area_sqm?.toFixed(1)} m² ·{" "}
                                  {id.slice(0, 5)}
                                </option>
                              );
                            })}
                          </select>
                        </label>
                        <button
                          type="button"
                          onClick={() =>
                            Assumptions(
                              Object.fromEntries(
                                Object.keys(b.assumptions).map((k) => [
                                  k,
                                  true,
                                ]),
                              ),
                            )
                          }
                        >
                          Try a conditional demo scenario
                        </button>
                        <p className="small muted">
                          Check only assumptions you want this draft to depend
                          on. These are not verified facts or real permissions.
                        </p>
                        {Object.entries(b.assumptions || {}).map(
                          ([key, label]) => (
                            <label key={key}>
                              <input
                                type="checkbox"
                                checked={assumptions[key] === true}
                                onChange={(e) =>
                                  Assumptions({
                                    ...assumptions,
                                    [key]: e.target.checked,
                                  })
                                }
                              />
                              {String(label)}
                            </label>
                          ),
                        )}
                      </details>
                    )}
                    <p className="muted small">
                      Simulated costs. Adjust priorities and compare trade-offs.
                    </p>
                    <details>
                      <summary>Priorities & intervention restrictions</summary>
                      {cfg?.uses.map((u: any) => (
                        <label key={u.id}>
                          {u.name}
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={weights[u.id] ?? u.weight}
                            onChange={(e) =>
                              W({ ...weights, [u.id]: +e.target.value })
                            }
                          />
                        </label>
                      ))}
                      {cfg?.interventions.map((i: any) => (
                        <label key={i.id}>
                          <input
                            type="checkbox"
                            checked={reject.includes(i.id)}
                            onChange={() => R(toggle(reject, i.id))}
                          />
                          Exclude {i.name}
                        </label>
                      ))}
                    </details>
                    <button className="primary" disabled={busy} onClick={run}>
                      <Sparkles size={18} />
                      {busy
                        ? "Evaluating possibilities…"
                        : "Find the best plan"}
                      <ArrowUpRight size={18} />
                    </button>
                  </section>
                </div>
                {p && (
                  <>
                    {dirty && (
                      <p className="comparison">
                        Results reflect the last completed run. Apply changed
                        inputs with “Find the best plan”.
                      </p>
                    )}
                    <div className="resulthead">
                      <div>
                        <p className="eyebrow">03 / RECOMMENDED SCENARIO</p>
                        <h2>A little investment. A wider purpose.</h2>
                      </div>
                      <span className="muted">
                        {p.eligible_portfolios} eligible / 64 portfolios
                        evaluated
                      </span>
                    </div>
                    <div className="metrics">
                      <div>
                        <small>
                          {b.is_synthetic
                            ? "NEW USES UNLOCKED"
                            : "CONDITIONAL USE OPTIONS"}
                        </small>
                        <strong>+{p.unlocked_uses.length}</strong>
                      </div>
                      <div>
                        <small>ESTIMATED INVESTMENT</small>
                        <strong>${p.total_cost_usd.toLocaleString()}</strong>
                      </div>
                      <div>
                        <small>BUDGET REMAINING</small>
                        <strong>
                          $
                          {(
                            p.scenario.budget_usd - p.total_cost_usd
                          ).toLocaleString()}
                        </strong>
                      </div>
                      <div>
                        <small>COST PER NEW USE</small>
                        <strong>
                          {p.unlocked_uses.length
                            ? "$" +
                              Math.round(
                                p.total_cost_usd / p.unlocked_uses.length,
                              ).toLocaleString()
                            : "—"}
                        </strong>
                      </div>
                    </div>
                    <div className="cards">
                      {p.feasibility_after.uses.map((u: any, i: number) => (
                        <article className="panel use" key={u.id}>
                          <span className={"status " + u.status}>
                            {u.status}
                            {u.conditional ? " · CONDITIONAL" : ""}
                          </span>
                          <h3>{u.name}</h3>
                          <p className="small muted">
                            Baseline {p.feasibility_before.uses[i].status} →{" "}
                            {u.status}
                          </p>
                          {u.checks.map((c: any) => (
                            <button
                              className="check"
                              key={c.capability}
                              onClick={() => F(c.capability)}
                            >
                              <span>
                                {c.status === "PASS"
                                  ? "✓"
                                  : c.status === "FAIL"
                                    ? "×"
                                    : "?"}
                              </span>
                              {c.capability.replaceAll("_", " ")}
                              <small>{c.status}</small>
                            </button>
                          ))}
                          <p className="gate">{u.external_gate}</p>
                        </article>
                      ))}
                    </div>
                    <section className="panel proposal">
                      <h2>Your proposed changes</h2>
                      {p.selected_interventions.length === 0 ? (
                        <p>
                          No eligible investment improves the modeled outcome.
                        </p>
                      ) : (
                        p.selected_interventions.map((i: any) => (
                          <div className="intervention" key={i.id}>
                            <Check size={18} />
                            <div>
                              <b>{i.name}</b>
                              <small>{i.cost_basis}</small>
                            </div>
                            <strong>${i.cost.toLocaleString()}</strong>
                          </div>
                        ))
                      )}
                      <p>{p.explanation}</p>
                      {p.reuse_proxy && (
                        <p className="comparison">
                          Reuse opportunity:{" "}
                          {Number(p.reuse_proxy.value || 0).toFixed(1)}{" "}
                          {p.reuse_proxy.unit}. {p.reuse_proxy.description}
                        </p>
                      )}
                      {p.runner_up && (
                        <details>
                          <summary>
                            Runner-up · $
                            {p.runner_up.total_cost_usd.toLocaleString()} ·{" "}
                            {p.runner_up.unlocked_uses.length} new uses
                          </summary>
                          <p>
                            {p.runner_up.selected_interventions
                              .map((i: any) => i.name)
                              .join(", ") || "No interventions"}
                          </p>
                        </details>
                      )}
                      {old && (
                        <p className="comparison">
                          Previous run: ${old.total_cost_usd.toLocaleString()} /{" "}
                          {old.unlocked_uses.length} new uses → current: $
                          {p.total_cost_usd.toLocaleString()} /{" "}
                          {p.unlocked_uses.length} new uses
                        </p>
                      )}
                      <div className="actions">
                        {["approved_draft", "rejected", "revise"].map((d) => (
                          <button
                            key={d}
                            onClick={async () => {
                              await api(
                                "/scenarios/" + p.run_id + "/decision",
                                { decision: d },
                              );
                              A(d);
                            }}
                          >
                            {d === "approved_draft"
                              ? "Approve draft"
                              : d === "rejected"
                                ? "Reject"
                                : "Request revision"}
                          </button>
                        ))}
                        <button
                          onClick={async () => {
                            try {
                              const r = await api(
                                "/scenarios/" + p.run_id + "/replay",
                                {},
                              );
                              ReplayMessage(
                                r.reproduced
                                  ? "Stored evidence and inputs reproduced this plan exactly."
                                  : "Replay differs; inspect engine configuration.",
                              );
                            } catch (e: any) {
                              ReplayMessage(e.message);
                            }
                          }}
                        >
                          Verify reproducibility
                        </button>
                        <a href={"/api/reports/" + p.run_id}>
                          <Download size={16} /> Markdown
                        </a>
                        <a href={"/api/reports/" + p.run_id + "?format=json"}>
                          JSON
                        </a>
                      </div>
                      {replayMessage && <p role="status">{replayMessage}</p>}
                      {decision && (
                        <p role="status">
                          Recorded: {decision}.{" "}
                          {decision === "revise"
                            ? "Adjust the constraints above and run a new scenario."
                            : ""}
                        </p>
                      )}
                    </section>
                    <Frontier scenario={scenario} onBudget={S} />
                  </>
                )}
              </>
            )}
            {tab === "Evidence" && (
              <>
                <Connections />
                <section className="panel">
                  <h2>Evidence register</h2>
                  {!b.is_synthetic && (
                    <div className="visualevidence">
                      <a
                        href={"https://my.matterport.com/show/?m=" + b.model_id}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Explore the interior scan ↗
                      </a>
                      <details>
                        <summary>Load Vexcel aerial image</summary>
                        <img
                          src="/api/integrations/vexcel/imagery"
                          loading="lazy"
                          alt="Vexcel aerial imagery around the selected Houston property"
                          style={{
                            width: "100%",
                            maxWidth: 700,
                            borderRadius: 8,
                          }}
                        />
                        <p className="small">
                          Context imagery centered on the scan coordinates. The
                          feasibility check uses the latest containing-parcel
                          attribute record, whose capture date may differ.
                        </p>
                      </details>
                    </div>
                  )}
                  <p>
                    {b.is_synthetic
                      ? "Every fixture observation is synthetic."
                      : "Real measurements cached locally from Matterport and Vexcel. A containing parcel was matched using the scan coordinates. Operating permissions and routes remain unverified."}
                  </p>
                  {!b.is_synthetic && (
                    <div className="comparison">
                      <b>Evidence sensitivity</b>
                      <p>
                        Withhold a source and rerun the planner to see which
                        constraints become UNKNOWN.
                      </p>
                      {["matterport", "vexcel"].map((x) => (
                        <label key={x}>
                          <input
                            type="checkbox"
                            checked={withheld.includes(x)}
                            onChange={() => Withheld(toggle(withheld, x))}
                          />
                          Withhold {x} evidence
                        </label>
                      ))}
                      <button disabled={busy} onClick={run}>
                        Reassess evidence
                      </button>
                      <p>
                        {p?.feasibility_after?.uses
                          .map((u: any) => u.name + ": " + u.status)
                          .join(" · ")}
                      </p>
                    </div>
                  )}
                  {b.evidence.map((e: any) => (
                    <article key={e.evidence_id}>
                      <h3>
                        {e.evidence_id} <span className="pill">{e.status}</span>
                      </h3>
                      <p>{e.observation}</p>
                      {e.value != null && (
                        <p>
                          Value: {Number(e.value).toFixed(2)} m²{" "}
                          {e.capture_date &&
                            " · Captured " + e.capture_date.slice(0, 10)}
                        </p>
                      )}
                      {e.source_ref && (
                        <a href={e.source_ref} target="_blank" rel="noreferrer">
                          Source reference ↗
                        </a>
                      )}
                    </article>
                  ))}
                  <h3>Data connection</h3>
                  <p>
                    Use the live sponsor browser above. Selecting a model does
                    not replace the authored demonstration graph; routes and
                    operating permissions still require verified evidence.
                  </p>
                </section>
              </>
            )}
            {tab === "Agent trace" && (
              <section className="panel">
                <h2>Decision workflow</h2>
                <p>
                  {p?.agent_mode} · {p?.explanation}
                </p>
                {p?.trace?.map((t: any, i: number) => (
                  <details className="trace" key={i}>
                    <summary>
                      {i + 1}. {t.tool}{" "}
                      <span className="status PASS">COMPLETE</span>
                    </summary>
                    <pre>{JSON.stringify(t.result, null, 2)}</pre>
                  </details>
                ))}
              </section>
            )}
            {tab === "Saved scenarios" && (
              <section className="panel">
                <h2>Scenario history</h2>
                {history.map((h) => (
                  <button
                    className="history"
                    key={h.run_id}
                    onClick={async () => {
                      const saved = await api("/scenarios/" + h.run_id);
                      if (saved.scenario.building_id !== b.building_id) {
                        E(
                          "Select the matching property before opening this saved scenario.",
                        );
                        return;
                      }
                      P(saved);
                      A(
                        typeof saved.decision === "object"
                          ? saved.decision.decision
                          : saved.decision,
                      );
                      Entry(saved.scenario.entry_room_id || undefined);
                      Assumptions(h.scenario.assumptions || {});
                      Withheld(h.scenario.withheld_sources || []);
                      S(h.scenario.budget_usd);
                      D(h.scenario.disabled_edges);
                      R(h.scenario.rejected_interventions);
                      W(h.scenario.use_weights);
                      N(h.scenario.name);
                      T("Planner");
                    }}
                  >
                    <b>{h.scenario.name}</b>
                    <span>
                      ${h.total_cost_usd.toLocaleString()} ·{" "}
                      {h.unlocked_uses.length} new uses ·{" "}
                      {new Date(h.created_at).toLocaleString()}
                    </span>
                  </button>
                ))}
              </section>
            )}
            <footer>
              Preliminary screening, subject to owner and professional review.
              PASS indicates modeled feasibility only.{" "}
              {b.is_synthetic
                ? "Synthetic data is used for this fixture."
                : "Sponsor measurements are cached; operational assumptions are explicitly conditional."}{" "}
              Intervention costs are simulated.
            </footer>
          </>
        )}
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
