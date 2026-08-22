import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/incidents", label: "Incident analysis" },
];

export function AppHeader() {
  return (
    <header className="site-header">
      <div className="brand">
        <Link href="/">Brasaland Digital</Link>
        <span className="brand-sub">Operations tools</span>
      </div>
      <nav aria-label="Main">
        <ul>
          {links.map((link) => (
            <li key={link.href}>
              <Link href={link.href}>{link.label}</Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
