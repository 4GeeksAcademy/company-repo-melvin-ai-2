import Link from "next/link";

export default function HomePage() {
  return (
    <div className="page">
      <h1>Brasaland internal web</h1>
      <p>
        Upload and analyze location incident CSVs for Operations and after-sales
        support without leaving the platform.
      </p>
      <p>
        <Link className="button" href="/incidents">
          Open incident analysis
        </Link>
      </p>
    </div>
  );
}
