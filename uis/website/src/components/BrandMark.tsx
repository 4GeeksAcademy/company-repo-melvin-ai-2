import Link from "next/link";

type BrandMarkProps = {
  as?: "link" | "text";
  href?: string;
  showBadge?: boolean;
  className?: string;
};

export function BrandMark({
  as = "link",
  href = "/",
  showBadge = true,
  className = "wordmark",
}: BrandMarkProps) {
  const label = (
    <>
      {showBadge ? (
        <span className="brand-mark" aria-hidden="true">
          B
        </span>
      ) : null}
      BRASALAND
    </>
  );

  if (as === "text") {
    return <p className={className}>{label}</p>;
  }

  return (
    <Link className={className} href={href}>
      {label}
    </Link>
  );
}
