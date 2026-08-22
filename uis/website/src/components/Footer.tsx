import Link from "next/link";

export function Footer() {
  return (
    <footer className="footer" id="contact">
      <div className="shell footer-grid">
        <div>
          <p className="wordmark footer-brand">BRASALAND</p>
          <p>Fire, flavor, and family since 2008.</p>
        </div>
        <div>
          <p className="footer-label">Visit or call</p>
          <a href="mailto:hello@brasaland.com">hello@brasaland.com</a>
          <a href="tel:+5741234567">Colombia · +57 4 123 4567</a>
          <a href="tel:+13051234567">Florida · +1 305 123 4567</a>
        </div>
        <div>
          <p className="footer-label">Stay connected</p>
          <a href="https://instagram.com/brasaland">Instagram</a>
          <a href="https://facebook.com/brasaland">Facebook</a>
          <Link href="/brasa-points">Join Brasa Points</Link>
        </div>
      </div>
      <div className="shell footer-bottom">
        <span>© 2026 Brasaland. All rights reserved.</span>
        <span>Colombia · Florida</span>
      </div>
    </footer>
  );
}
