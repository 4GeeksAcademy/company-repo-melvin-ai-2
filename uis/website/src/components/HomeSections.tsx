import Link from "next/link";
import { locations, pillars } from "@/data/site";

export function Hero() {
  return (
    <section className="hero">
      <div className="hero-glow" aria-hidden="true" />
      <div className="shell hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Born in Medellín · Grilling since 2008</p>
          <h1>
            The taste of the grill,
            <em> in every bite.</em>
          </h1>
          <p className="hero-lede">
            Fourteen restaurants. Two countries. One passion for honest fire,
            generous plates, and the people around the table.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/brasa-points">
              Join Brasa Points <span aria-hidden="true">→</span>
            </Link>
            <a className="text-link" href="#locations">
              Find your table
            </a>
          </div>
          <div className="hero-stats" aria-label="Brasaland at a glance">
            <div>
              <strong>14</strong>
              <span>restaurants</span>
            </div>
            <div>
              <strong>2</strong>
              <span>countries</span>
            </div>
            <div>
              <strong>18</strong>
              <span>years of fire</span>
            </div>
          </div>
        </div>
        <div className="grill-card" aria-label="Fresh grilled food at Brasaland">
          <div className="grill-rings" aria-hidden="true" />
          <p>Fresh from the grill</p>
          <strong>Good food starts with real fire.</strong>
          <span>Prepared to order, served with warmth.</span>
        </div>
      </div>
    </section>
  );
}

export function Story() {
  return (
    <section className="section story" id="story">
      <div className="shell story-grid">
        <div>
          <p className="eyebrow">Our story</p>
          <h2>A family dream that kept its seat at the table.</h2>
        </div>
        <div className="story-copy">
          <p>
            Brasaland began in Medellín with a simple promise: share the
            authentic taste of grilled meat with consistent quality and warm
            service.
          </p>
          <p>
            Today we serve Colombia and Florida, but the recipe remains the
            same—fresh ingredients, traditional techniques, and care in every
            dish.
          </p>
        </div>
      </div>
    </section>
  );
}

export function Pillars() {
  return (
    <section className="section section-cream" aria-labelledby="pillars-title">
      <div className="shell">
        <p className="eyebrow">What makes us unique</p>
        <h2 id="pillars-title">The Brasaland standard.</h2>
        <div className="pillar-grid">
          {pillars.map((pillar) => (
            <article className="pillar-card" key={pillar.number}>
              <span>{pillar.number}</span>
              <h3>{pillar.title}</h3>
              <p>{pillar.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function MenuFeature() {
  return (
    <section className="section menu-feature" id="menu">
      <div className="shell menu-grid">
        <div className="menu-art" aria-hidden="true">
          <span>FIRE</span>
          <span>FLAVOR</span>
          <span>FAMILY</span>
        </div>
        <div>
          <p className="eyebrow">Made for the table</p>
          <h2>Grilled favorites, generous sides, no shortcuts.</h2>
          <p>
            From our signature picanha to crisp sides and family combos, every
            plate is prepared to order and built for sharing.
          </p>
          <p className="notice">
            Want to place an order? Call your favorite location or visit us
            directly. Online ordering coming soon!
          </p>
        </div>
      </div>
    </section>
  );
}

export function Locations() {
  return (
    <section className="section locations" id="locations">
      <div className="shell">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Our locations</p>
            <h2>There is a fire near you.</h2>
          </div>
          <p>Open Monday–Sunday · 11:00 AM–10:00 PM</p>
        </div>
        <div className="location-grid">
          {Object.entries(locations).map(([country, names]) => (
            <article className="location-card" key={country}>
              <p className="location-count">{names.length} restaurants</p>
              <h3>{country}</h3>
              <p>
                {country === "Colombia"
                  ? "Medellín · Bogotá · Cali"
                  : "Miami · Orlando"}
              </p>
              <ul>
                {names.map((name) => (
                  <li key={name}>{name}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Loyalty() {
  return (
    <section className="loyalty">
      <div className="shell loyalty-grid">
        <div>
          <p className="eyebrow eyebrow-light">Brasa Points</p>
          <h2>Every visit should bring something back.</h2>
          <p>
            Earn one point for every $10,000 COP or $5 USD, then turn your
            visits into discounts, free dishes, and member-only offers.
          </p>
        </div>
        <div className="loyalty-action">
          <span>Free to join · 100% digital</span>
          <Link className="button button-light" href="/brasa-points">
            Become a member <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
