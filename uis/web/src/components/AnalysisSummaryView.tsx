import type { AnalysisSummary } from "@/lib/api";

type AnalysisSummaryViewProps = {
  summary: AnalysisSummary;
};

export function AnalysisSummaryView({ summary }: AnalysisSummaryViewProps) {
  const { totals, invalid_breakdown, by_category, by_status, satisfaction } =
    summary;
  const hasInvalid = totals.invalid_records > 0;

  return (
    <div className="summary">
      <section className="panel" aria-labelledby="totals-heading">
        <h2 id="totals-heading">General metrics</h2>
        <p className="muted">Source: {summary.source_file}</p>
        <ul className="stat-list">
          <li>
            <span>Total records</span>
            <strong>{totals.total_records}</strong>
          </li>
          <li>
            <span>Valid records</span>
            <strong>{totals.valid_records}</strong>
          </li>
          <li>
            <span>Invalid / incomplete</span>
            <strong>{totals.invalid_records}</strong>
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
            <strong>{invalid_breakdown.missing_location_id}</strong>
          </li>
          <li>
            <span>Invalid or missing category</span>
            <strong>{invalid_breakdown.invalid_or_missing_category}</strong>
          </li>
          <li>
            <span>Empty description</span>
            <strong>{invalid_breakdown.empty_description}</strong>
          </li>
          <li>
            <span>Closed case, no score</span>
            <strong>{invalid_breakdown.closed_case_no_score}</strong>
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
                <td>{row.count}</td>
                <td>{row.percentage.toFixed(1)}%</td>
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
                <td>{row.count}</td>
                <td>{row.percentage.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel" aria-labelledby="satisfaction-heading">
        <h2 id="satisfaction-heading">Satisfaction index</h2>
        <p>
          Scored cases: {satisfaction.scored_cases} of{" "}
          {satisfaction.closed_cases}
        </p>
        <p>
          Average score:{" "}
          <strong>
            {satisfaction.average_score === null
              ? "—"
              : satisfaction.average_score.toFixed(2)}{" "}
            / 5.00
          </strong>
        </p>
        <ul className="stat-list">
          {satisfaction.by_score.map((row) => (
            <li key={row.score}>
              <span>
                Score {row.score} ({row.label})
              </span>
              <strong>{row.count}</strong>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
