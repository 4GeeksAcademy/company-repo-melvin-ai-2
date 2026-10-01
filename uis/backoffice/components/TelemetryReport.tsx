type MetricRow = Record<string, string | number>;

type MetricColumn = {
  key: string;
  label: string;
};

type TelemetryReportProps = {
  period: { from: string; to: string };
  metrics: {
    events_per_day: MetricRow[];
    error_rate_by_type: MetricRow[];
    auth_failure_rate: MetricRow[];
    latency_by_route: MetricRow[];
  };
};

const TABLES: Array<{
  key: keyof TelemetryReportProps["metrics"];
  title: string;
  columns: MetricColumn[];
}> = [
  {
    key: "events_per_day",
    title: "Events per day",
    columns: [
      { key: "date", label: "Date" },
      { key: "event_count", label: "Events" },
    ],
  },
  {
    key: "error_rate_by_type",
    title: "Error rate by type",
    columns: [
      { key: "date", label: "Date" },
      { key: "event_type", label: "Event type" },
      { key: "error_count", label: "Errors" },
      { key: "total", label: "Events that day" },
      { key: "error_rate", label: "Error rate" },
    ],
  },
  {
    key: "auth_failure_rate",
    title: "Login failure rate",
    columns: [
      { key: "date", label: "Date" },
      { key: "failed", label: "Failed" },
      { key: "attempts", label: "Attempts" },
      { key: "auth_failure_rate", label: "Failure rate" },
    ],
  },
  {
    key: "latency_by_route",
    title: "Latency by route",
    columns: [
      { key: "date", label: "Date" },
      { key: "route", label: "Route" },
      { key: "mean_duration_ms", label: "Mean duration (ms)" },
    ],
  },
];

export function TelemetryReport({ period, metrics }: TelemetryReportProps) {
  return (
    <section aria-labelledby="telemetry-report-title">
      <h1 id="telemetry-report-title">Telemetry report</h1>
      <p>
        System behaviour for this window:{" "}
        <time dateTime={period.from}>{period.from}</time>
        {" to "}
        <time dateTime={period.to}>{period.to}</time>
      </p>
      {TABLES.map((table) => (
        <MetricTable
          key={table.key}
          title={table.title}
          columns={table.columns}
          rows={metrics[table.key]}
        />
      ))}
    </section>
  );
}

function MetricTable({
  title,
  columns,
  rows,
}: {
  title: string;
  columns: MetricColumn[];
  rows: MetricRow[];
}) {
  const headingId = title.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId}>{title}</h2>
      {rows.length === 0 ? (
        <p>No rows in this window.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key} scope="col">
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${headingId}-${index}`}>
                  {columns.map((column) => (
                    <td key={column.key}>{formatCell(row[column.key])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function formatCell(value: string | number | undefined): string {
  if (value === undefined || value === null) return "—";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(3);
  }
  return value;
}
