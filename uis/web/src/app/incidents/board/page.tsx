import { IncidentBoard } from "@/components/IncidentBoard";

export default function IncidentBoardPage() {
  return (
    <div className="page">
      <h1>Incident board</h1>
      <p>Open, in progress, resolved, and discarded incidents across Brasaland.</p>
      <IncidentBoard />
    </div>
  );
}
