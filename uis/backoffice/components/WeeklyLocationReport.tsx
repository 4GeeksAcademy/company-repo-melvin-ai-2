"use client";

import { useCallback, useEffect, useState } from "react";
import {
  REPORT_COLUMNS,
  formatReportCell,
  loadWeeklyLocationPerformance,
  type WeeklyReport,
} from "@/lib/weeklyReport";

export function WeeklyLocationReport() {
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [weekInput, setWeekInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (weekStart?: string) => {
    setLoading(true);
    setError(null);
    try {
      const body = await loadWeeklyLocationPerformance(weekStart);
      setReport(body);
      if (body.week_start) setWeekInput(body.week_start);
    } catch (err) {
      if (err instanceof Error && err.name === "AuthSessionError") return;
      setReport(null);
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the Brasaland service. Check your connection and try again.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- load the latest week after sign-in
    void load().catch(() => {
      if (cancelled) return;
    });
    return () => {
      cancelled = true;
    };
  }, [load]);

  return (
    <section className="weekly-report" aria-labelledby="weekly-location-report-title">
      <h1 id="weekly-location-report-title">Weekly location cost and waste</h1>
      <p>
        How much each kitchen spent, how much it wasted, and how often stock
        ran low or a supplier price jumped. Amounts stay in that kitchen&apos;s
        currency. Waste Ratio is waste cost divided by purchase cost, so 0%
        means there was no waste or there were no purchases to compare.
      </p>
      <form
        className="weekly-report-week"
        onSubmit={(event) => {
          event.preventDefault();
          void load(weekInput || undefined);
        }}
      >
        <label htmlFor="week-start">
          Week starting Monday
          <input
            id="week-start"
            type="date"
            value={weekInput}
            onChange={(event) => setWeekInput(event.target.value)}
          />
        </label>
        <button type="submit">Show week</button>
      </form>
      {loading ? <p>Loading the weekly report.</p> : null}
      {error ? <p role="alert">{error}</p> : null}
      {!loading && report && !report.week_start ? (
        <p>No weekly report has been loaded yet.</p>
      ) : null}
      {!loading && report?.week_start ? (
        <>
          <p>
            Week of <time dateTime={report.week_start}>{report.week_start}</time>
          </p>
          {report.locations.length === 0 ? (
            <p>No location totals for this week.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <caption>
                  Weekly location cost and waste for the week of {report.week_start}
                </caption>
                <thead>
                  <tr>
                    {REPORT_COLUMNS.map((column) => (
                      <th key={column.key} scope="col">
                        {column.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {report.locations.map((row) => (
                    <tr key={row.location_id}>
                      {REPORT_COLUMNS.map((column) => (
                        <td key={column.key}>{formatReportCell(column.key, row)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : null}
    </section>
  );
}
