"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SessionNav, AUTH_PUBLIC_PATHS } from "@repo/auth";

const links = [
  { href: "/", label: "Home" },
  { href: "/incidents", label: "Incident analysis" },
];

export function AppHeader() {
  const pathname = usePathname() || "/";
  const isPublic = AUTH_PUBLIC_PATHS.has(pathname);

  return (
    <header className="site-header">
      <div className="brand">
        <Link href="/">Brasaland Digital</Link>
        <span className="brand-sub">Operations tools</span>
      </div>
      {isPublic ? (
        <nav aria-label="Account">
          <ul>
            <li>
              <Link href="/login">Sign in</Link>
            </li>
            <li>
              <Link href="/register">Register</Link>
            </li>
          </ul>
        </nav>
      ) : (
        <nav aria-label="Main">
          <ul>
            {links.map((link) => (
              <li key={link.href}>
                <Link href={link.href}>{link.label}</Link>
              </li>
            ))}
            <li>
              <SessionNav />
            </li>
          </ul>
        </nav>
      )}
    </header>
  );
}
