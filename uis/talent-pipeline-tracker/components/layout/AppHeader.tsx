import Link from "next/link";

export function AppHeader() {
  return (
    <header className="border-b border-stone-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#c0392b] text-lg font-bold text-white">
            B
          </div>
          <div>
            <Link href="/" className="text-lg font-semibold text-stone-900 hover:text-[#c0392b]">
              Brasaland Talent Pipeline
            </Link>
            <p className="text-xs text-stone-500">
              People &amp; Talent · 14 locations across Colombia &amp; Florida
            </p>
          </div>
        </div>
        <nav className="flex items-center gap-3">
          <Link
            href="/"
            className="rounded-md px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100"
          >
            Candidates
          </Link>
          <Link
            href="/candidates/new"
            className="rounded-md bg-[#c0392b] px-4 py-2 text-sm font-medium text-white hover:bg-[#a93226]"
          >
            Add Candidate
          </Link>
        </nav>
      </div>
    </header>
  );
}
