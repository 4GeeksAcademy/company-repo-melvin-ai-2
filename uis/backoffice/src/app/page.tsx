import Link from "next/link";
import { OperationsDashboard } from "@/components/OperationsDashboard";

export default function Home() {
  return (
    <div className="workspace">
      <aside className="sidebar">
        <Link className="admin-brand" href="/" aria-label="Brasaland backoffice home">
          <span aria-hidden="true">B</span>
          <div>
            <strong>BRASALAND</strong>
            <small>Backoffice</small>
          </div>
        </Link>
        <nav aria-label="Backoffice navigation">
          <Link className="active" href="/" aria-current="page">
            <span aria-hidden="true">⌁</span> Overview
          </Link>
          <a href="#locations">
            <span aria-hidden="true">⌖</span> Locations
          </a>
          <a href="#sales">
            <span aria-hidden="true">↗</span> Sales
          </a>
          <a href="#waste">
            <span aria-hidden="true">△</span> Waste
          </a>
          <a href="#people">
            <span aria-hidden="true">◎</span> People &amp; Talent
          </a>
        </nav>
        <div className="sidebar-foot">
          <span>MR</span>
          <div>
            <strong>Mariana Restrepo</strong>
            <small>Operations admin</small>
          </div>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="topbar">
          <span>Internal company workspace</span>
          <button type="button" aria-label="Notifications">
            2
          </button>
        </header>
        <main>
          <div className="welcome">
            <div>
              <p className="kicker">Tuesday, July 21</p>
              <h1>Good afternoon, Mariana.</h1>
              <p>Here is what is happening across Brasaland today.</p>
            </div>
            <div className="market-pill">
              <span aria-hidden="true">●</span> Colombia + Florida
            </div>
          </div>
          <OperationsDashboard />
          <section id="people" className="people-panel" aria-label="People and talent">
            <h2>People &amp; Talent</h2>
            <p>
              Talent and hiring insights will appear here in the next milestone.
            </p>
          </section>
        </main>
      </div>
    </div>
  );
}
