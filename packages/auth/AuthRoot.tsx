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

export function AuthRoot({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "/";
  if (AUTH_PUBLIC_PATHS.has(pathname)) {
    return <>{children}</>;
  }
  return <AuthGuard>{children}</AuthGuard>;
}
