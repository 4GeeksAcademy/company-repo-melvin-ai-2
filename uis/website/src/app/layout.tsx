import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Brasaland | Fire, flavor and family",
    template: "%s | Brasaland",
  },
  description:
    "Grilled food and warm hospitality across 14 restaurants in Colombia and Florida.",
  metadataBase: new URL("https://brasaland.com"),
};

const restaurantSchema = {
  "@context": "https://schema.org",
  "@type": "Restaurant",
  name: "Brasaland",
  description: "Grilled food restaurant chain in Colombia and the United States",
  url: "https://brasaland.com",
  foundingDate: "2008",
  servesCuisine: ["Grilled food", "Colombian cuisine"],
  priceRange: "$$",
  numberOfLocations: 14,
  contactPoint: {
    "@type": "ContactPoint",
    telephone: "+57-4-123-4567",
    contactType: "customer service",
    availableLanguage: ["English", "Spanish"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(restaurantSchema) }}
        />
      </body>
    </html>
  );
}
