import { IncidentReportForm } from "@/components/IncidentReportForm";

export default function ReportIncidentPage() {
  return (
    <div className="page">
      <h1>Report an incident</h1>
      <p>
        Location managers and the headquarters team use this form. The branch
        names are the Brasaland locations, including Central.
      </p>
      <IncidentReportForm />
    </div>
  );
}
