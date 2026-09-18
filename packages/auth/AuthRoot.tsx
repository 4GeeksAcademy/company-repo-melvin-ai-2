"use client";

import { usePathname } from "next/navigation";
import { AuthGuard } from "./AuthGuard";
import "./styles.css";

export const AUTH_PUBLIC_PATHS = new Set([
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
]);

export function AuthRoot({
  children,
  hasSessionCookie = false,
}: {
  children: React.ReactNode;
  hasSessionCookie?: boolean;
}) {
  const pathname = usePathname() || "/";
  if (AUTH_PUBLIC_PATHS.has(pathname)) {
    return <>{children}</>;
  }
  return (
    <AuthGuard hasSessionCookie={hasSessionCookie}>{children}</AuthGuard>
  );
}
