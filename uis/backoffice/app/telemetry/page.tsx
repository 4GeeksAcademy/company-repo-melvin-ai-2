import { getBrasalandApiBase } from "@repo/auth";
import { BackofficeShell } from "@/components/BackofficeShell";
import { TelemetryReport } from "@/components/TelemetryReport";

export const dynamic = "force-dynamic";

type ReportBody = {
  period: { from: string; to: string };
  metrics: {
    events_per_day: Array<Record<string, string | number>>;
    error_rate_by_type: Array<Record<string, string | number>>;
    auth_failure_rate: Array<Record<string, string | number>>;
    latency_by_route: Array<Record<string, string | number>>;
  };
};

export default async function TelemetryPage() {
  const report = await loadReport();
  return (
    <BackofficeShell>
      {report.ok ? (
        <TelemetryReport period={report.body.period} metrics={report.body.metrics} />
      ) : (
        <section aria-labelledby="telemetry-report-title">
          <h1 id="telemetry-report-title">Telemetry report</h1>
          <p role="alert">{report.message}</p>
        </section>
      )}
    </BackofficeShell>
  );
}

async function loadReport(): Promise<
  { ok: true; body: ReportBody } | { ok: false; message: string }
> {
  try {
    const response = await fetch(`${getBrasalandApiBase()}/telemetry/report`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return {
        ok: false,
        message:
          "The telemetry report is unavailable. Try again or contact hello@brasaland.com.",
      };
    }
    return { ok: true, body: (await response.json()) as ReportBody };
  } catch {
    return {
      ok: false,
      message:
        "Could not reach the Brasaland service. Check your connection and try again.",
    };
  }
}
