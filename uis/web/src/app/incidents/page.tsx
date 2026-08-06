import { IncidentAnalyzer } from "@/components/IncidentAnalyzer";

export default function IncidentsPage() {
  return (
    <div className="page">
      <h1>Incident analysis</h1>
      <p>
        Upload <code>incidents-brasaland.csv</code> (or another Brasaland
        incidents export). Analysis runs on the company API — files stay
        internal.
      </p>
      <IncidentAnalyzer />
    </div>
  );
}
