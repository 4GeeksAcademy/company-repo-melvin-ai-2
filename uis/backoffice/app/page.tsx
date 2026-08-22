import { BackofficeShell } from "@/components/BackofficeShell";
import { OperationsDashboard } from "@/components/OperationsDashboard";

export default function Home() {
  return (
    <BackofficeShell>
      <div className="welcome">
        <div>
          <p className="kicker">Operations overview</p>
          <h1>Good afternoon, Mariana.</h1>
          <p>Here is what is happening across Brasaland today.</p>
        </div>
        <div className="market-pill">
          <span aria-hidden="true">●</span> Colombia + Florida
        </div>
      </div>
      <OperationsDashboard />
    </BackofficeShell>
  );
}
