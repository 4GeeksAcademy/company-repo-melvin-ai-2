import type { Metadata } from "next";
import { cookies } from "next/headers";
import { AuthRoot, SESSION_COOKIE } from "@repo/auth";
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
        <AuthRoot hasSessionCookie={hasSessionCookie}>{children}</AuthRoot>
      </body>
    </html>
  );
}
