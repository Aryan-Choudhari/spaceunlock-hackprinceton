import { useState } from "react";
export default function Frontier({
  scenario,
  onBudget,
}: {
  scenario: any;
  onBudget: (n: number) => void;
}) {
  const [data, D] = useState<any>(),
    [busy, B] = useState(false),
    [error, E] = useState("");
  async function load() {
    B(true);
    E("");
    try {
      const r = await fetch("/api/scenarios/frontier", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      if (!r.ok) throw Error("Could not calculate budget comparison");
      D(await r.json());
    } catch (e: any) {
      E(e.message);
    } finally {
      B(false);
    }
  }
  return (
    <section className="panel" style={{ marginTop: 20 }}>
      <div className="panelhead">
        <div>
          <p className="eyebrow">BUDGET SENSITIVITY</p>
          <h2>Where does the next dollar matter?</h2>
        </div>
        <button onClick={load} disabled={busy}>
          {busy ? "Comparing…" : "Compare budgets"}
        </button>
      </div>
      <p className="small muted">
        Recompute ten budget scenarios with the current evidence, assumptions
        and exclusions.
      </p>
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <svg
            viewBox="0 0 700 170"
            style={{ width: "100%" }}
            role="img"
            aria-label="Number of newly unlocked uses at different budgets"
          >
            {[0, 1, 2, 3, 4].map((n) => (
              <g key={n}>
                <line
                  x1="40"
                  x2="680"
                  y1={140 - n * 30}
                  y2={140 - n * 30}
                  stroke="#dce4d7"
                />
                <text x="15" y={145 - n * 30} fontSize="12">
                  {n}
                </text>
              </g>
            ))}
            <polyline
              points={data.points
                .map(
                  (p: any, i: number) =>
                    `${50 + i * 68},${140 - p.unlocked * 30}`,
                )
                .join(" ")}
              fill="none"
              stroke="#39754f"
              strokeWidth="3"
            />
            {data.points.map((p: any, i: number) => (
              <g key={p.budget}>
                <circle
                  cx={50 + i * 68}
                  cy={140 - p.unlocked * 30}
                  r="5"
                  fill="#39754f"
                />
                <text x={50 + i * 68} y="163" textAnchor="middle" fontSize="10">
                  ${p.budget / 1000}k
                </text>
              </g>
            ))}
          </svg>
          <div className="budgetpoints">
            {data.points.map((p: any) => (
              <button key={p.budget} onClick={() => onBudget(p.budget)}>
                ${p.budget.toLocaleString()}
                <small>
                  {p.unlocked} uses · ${p.cost.toLocaleString()} spent
                </small>
              </button>
            ))}
          </div>
          <p className="small muted">
            Select a budget to apply it, then rerun the planner. Displayed
            comparison is a snapshot of inputs when calculated.
          </p>
        </>
      )}
    </section>
  );
}
