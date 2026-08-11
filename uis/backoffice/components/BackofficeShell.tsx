"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type BackofficeShellProps = {
  children: React.ReactNode;
};

export function BackofficeShell({ children }: BackofficeShellProps) {
  const pathname = usePathname();

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
          <Link
            className={pathname === "/" ? "active" : undefined}
            href="/"
            aria-current={pathname === "/" ? "page" : undefined}
          >
            <span aria-hidden="true">⌁</span> Overview
          </Link>
          <Link
            className={pathname?.startsWith("/suppliers") ? "active" : undefined}
            href="/suppliers"
            aria-current={pathname?.startsWith("/suppliers") ? "page" : undefined}
          >
            <span aria-hidden="true">▣</span> Suppliers
          </Link>
          <Link href="/#locations">
            <span aria-hidden="true">⌖</span> Locations
          </Link>
          <Link href="/#sales">
            <span aria-hidden="true">↗</span> Sales
          </Link>
          <Link href="/#waste">
            <span aria-hidden="true">△</span> Waste
          </Link>
          <Link href="/#people">
            <span aria-hidden="true">◎</span> People &amp; Talent
          </Link>
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
        <main>{children}</main>
      </div>
    </div>
  );
}
