import Link from "next/link";

interface BackLinkProps {
  href: string;
  label?: string;
}

export function BackLink({ href, label = "Back to candidates" }: BackLinkProps) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 text-sm font-medium text-[#c0392b] hover:text-[#a93226]"
    >
      <span aria-hidden="true">←</span>
      {label}
    </Link>
  );
}
