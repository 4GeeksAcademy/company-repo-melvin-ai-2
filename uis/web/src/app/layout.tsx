import type { Metadata } from "next";
import { AuthRoot } from "@repo/auth";
import { AppHeader } from "@/components/AppHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "Brasaland Web Tools",
  description: "Internal Brasaland web tools for operations and after-sales.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthRoot>
          <a className="skip-link" href="#main">
            Skip to content
          </a>
          <AppHeader />
          <main id="main">{children}</main>
        </AuthRoot>
      </body>
    </html>
  );
}
