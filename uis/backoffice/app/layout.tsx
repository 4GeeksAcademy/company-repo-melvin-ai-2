import type { Metadata } from "next";
import { cookies } from "next/headers";
import { AuthRoot, SESSION_COOKIE } from "@repo/auth";
import {
  TelemetryErrorBoundary,
  TelemetryRoot,
} from "@/components/TelemetryRoot";
import "./globals.css";

export const metadata: Metadata = {
  title: "Operations Overview | Brasaland Backoffice",
  description: "Brasaland internal operations workspace.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const hasSessionCookie =
    (await cookies()).get(SESSION_COOKIE)?.value === "1";

  return (
    <html lang="en">
      <body>
        <TelemetryRoot>
          <TelemetryErrorBoundary>
            <AuthRoot hasSessionCookie={hasSessionCookie}>{children}</AuthRoot>
          </TelemetryErrorBoundary>
        </TelemetryRoot>
      </body>
    </html>
  );
}
