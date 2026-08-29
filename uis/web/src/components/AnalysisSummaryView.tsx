import type { AnalysisSummary } from "@/lib/api";

type AnalysisSummaryViewProps = {
  summary: AnalysisSummary;
};

const EMPTY_BREAKDOWN = {
  missing_location_id: 0,
  invalid_or_missing_category: 0,
  empty_description: 0,
  closed_case_no_score: 0,
  missing_reporter_id: 0,
  score_out_of_range: 0,
};

export function AnalysisSummaryView({ summary }: AnalysisSummaryViewProps) {
  const totals = summary?.totals ?? {
    total_records: 0,
    valid_records: 0,
    invalid_records: 0,
  };
  const invalid_breakdown = summary?.invalid_breakdown ?? EMPTY_BREAKDOWN;
  const by_category = summary?.by_category ?? [];
  const by_status = summary?.by_status ?? [];
  const satisfaction = summary?.satisfaction ?? {
    scored_cases: 0,
    closed_cases: 0,
    average_score: null,
    by_score: [],
  };
  const hasInvalid = (totals.invalid_records ?? 0) > 0;

  return (
    <div className="summary">
      <section className="panel" aria-labelledby="totals-heading">
        <h2 id="totals-heading">General metrics</h2>
        <p className="muted">Source: {summary?.source_file || "—"}</p>
        <ul className="stat-list">
          <li>
            <span>Total records</span>
            <strong>{totals.total_records ?? 0}</strong>
          </li>
          <li>
            <span>Valid records</span>
            <strong>{totals.valid_records ?? 0}</strong>
          </li>
          <li>
            <span>Invalid / incomplete</span>
            <strong>{totals.invalid_records ?? 0}</strong>
          </li>
        </ul>
      </section>

      <section
        className={`panel${hasInvalid ? " panel--warning" : ""}`}
        aria-labelledby="invalid-heading"
      >
        <h2 id="invalid-heading">Invalid records</h2>
        {hasInvalid ? (
          <p role="status">
            This file includes {totals.invalid_records} invalid record
            {totals.invalid_records === 1 ? "" : "s"}. They were counted and
            excluded from the main analysis.
          </p>
        ) : (
          <p role="status">No invalid records detected.</p>
        )}
        <ul className="stat-list">
          <li>
            <span>Missing location_id</span>
            <strong>{invalid_breakdown.missing_location_id ?? 0}</strong>
          </li>
          <li>
            <span>Invalid or missing category</span>
            <strong>{invalid_breakdown.invalid_or_missing_category ?? 0}</strong>
          </li>
          <li>
            <span>Empty description</span>
            <strong>{invalid_breakdown.empty_description ?? 0}</strong>
          </li>
          <li>
            <span>Missing reporter_id</span>
            <strong>{invalid_breakdown.missing_reporter_id ?? 0}</strong>
          </li>
          <li>
            <span>Closed case, no score</span>
            <strong>{invalid_breakdown.closed_case_no_score ?? 0}</strong>
          </li>
          <li>
            <span>Satisfaction score out of range</span>
            <strong>{invalid_breakdown.score_out_of_range ?? 0}</strong>
          </li>
        </ul>
      </section>

      <section className="panel" aria-labelledby="category-heading">
        <h2 id="category-heading">Breakdown by category</h2>
        <table>
          <thead>
            <tr>
              <th scope="col">Category</th>
              <th scope="col">Count</th>
              <th scope="col">%</th>
            </tr>
          </thead>
          <tbody>
            {by_category.map((row) => (
              <tr key={row.category}>
                <td>{row.category}</td>
                <td>{row.count ?? 0}</td>
                <td>{Number(row.percentage ?? 0).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel" aria-labelledby="status-heading">
        <h2 id="status-heading">Breakdown by status</h2>
        <table>
          <thead>
            <tr>
              <th scope="col">Status</th>
              <th scope="col">Count</th>
              <th scope="col">%</th>
            </tr>
          </thead>
          <tbody>
            {by_status.map((row) => (
              <tr key={row.status}>
                <td>{row.status}</td>
                <td>{row.count ?? 0}</td>
                <td>{Number(row.percentage ?? 0).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel" aria-labelledby="satisfaction-heading">
        <h2 id="satisfaction-heading">Satisfaction index</h2>
        <p>
          Scored cases: {satisfaction.scored_cases ?? 0} of{" "}
          {satisfaction.closed_cases ?? 0}
        </p>
        <p>
          Average score:{" "}
          <strong>
            {satisfaction.average_score == null
              ? "—"
              : Number(satisfaction.average_score).toFixed(2)}{" "}
            / 5.00
          </strong>
        </p>
        <ul className="stat-list">
          {(satisfaction.by_score ?? []).map((row) => (
            <li key={row.score}>
              <span>
                Score {row.score} ({row.label})
              </span>
              <strong>{row.count ?? 0}</strong>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
