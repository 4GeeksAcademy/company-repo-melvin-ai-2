"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/backoffice/inventory/products", label: "Ingredients" },
  { href: "/backoffice/inventory/orders/inbound", label: "Log delivery" },
  { href: "/backoffice/inventory/orders/outbound", label: "Log consumption" },
  { href: "/backoffice/inventory/orders", label: "Order history" },
] as const;

export function InventoryNav() {
  const pathname = usePathname();

  return (
    <nav className="inventory-subnav" aria-label="Ingredient inventory">
      {LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={active ? "active" : undefined}
            aria-current={active ? "page" : undefined}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
