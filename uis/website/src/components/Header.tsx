import Link from "next/link";

export function Header() {
  return (
    <header className="site-header">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <div className="shell nav-shell">
        <Link className="wordmark" href="/" aria-label="Brasaland home">
          <span className="brand-mark" aria-hidden="true">
            B
          </span>
          BRASALAND
        </Link>
        <nav aria-label="Main navigation">
          <Link href="/#story">Story</Link>
          <Link href="/#locations">Locations</Link>
          <Link href="/#menu">Menu</Link>
          <Link href="/#contact">Contact</Link>
          <Link className="nav-cta" href="/brasa-points">
            Brasa Points
          </Link>
        </nav>
      </div>
    </header>
  );
}
