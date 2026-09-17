"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function BackofficeNav() {
  const pathname = usePathname();

  return (
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
      <Link
        className={
          pathname?.startsWith("/backoffice/inventory") ? "active" : undefined
        }
        href="/backoffice/inventory/products"
        aria-current={
          pathname?.startsWith("/backoffice/inventory") ? "page" : undefined
        }
      >
        <span aria-hidden="true">▤</span> Inventory
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
  );
}
