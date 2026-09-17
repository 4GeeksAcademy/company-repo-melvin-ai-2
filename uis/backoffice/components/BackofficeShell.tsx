import Link from "next/link";
import { SessionNav } from "@repo/auth";
import { BackofficeNav } from "./BackofficeNav";

type BackofficeShellProps = {
  children: React.ReactNode;
};

export function BackofficeShell({ children }: BackofficeShellProps) {
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
        <BackofficeNav />
        <div className="sidebar-foot">
          <span>LF</span>
          <div>
            <strong>Signed in</strong>
            <small>Brasaland operator</small>
          </div>
          <SessionNav />
        </div>
      </aside>

      <div className="workspace-main">
        <header className="topbar">
          <span>Internal company workspace</span>
          <button type="button" aria-label="Notifications">
            2
          </button>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
