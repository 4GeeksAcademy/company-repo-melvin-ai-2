import { BackofficeShell } from "@/components/BackofficeShell";
import { WeeklyLocationReport } from "@/components/WeeklyLocationReport";

export const dynamic = "force-dynamic";

export default function ReportingPage() {
  return (
    <BackofficeShell>
      <WeeklyLocationReport />
    </BackofficeShell>
  );
}
