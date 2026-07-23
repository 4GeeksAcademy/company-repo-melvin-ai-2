import type { Metadata } from "next";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { LoyaltyForm } from "@/components/LoyaltyForm";

export const metadata: Metadata = {
  title: "Join Brasa Points",
  description:
    "Join Brasaland's digital loyalty program and earn rewards at all 14 locations.",
};

export default function BrasaPointsPage() {
  return (
    <>
      <Header />
      <main id="main" className="form-page">
        <section className="form-intro">
          <div className="shell narrow">
            <p className="eyebrow">Brasa Points</p>
            <h1>More flavor. More rewards. One simple account.</h1>
            <p>
              Join free and earn points at any Brasaland restaurant in Colombia
              or Florida. Membership is available to guests 18 and older.
            </p>
            <p className="notice">
              Want to place an order? Call your favorite location or visit us
              directly. Online ordering coming soon!
            </p>
          </div>
        </section>
        <section className="shell narrow form-section" aria-label="Registration form">
          <LoyaltyForm />
        </section>
      </main>
      <Footer />
    </>
  );
}
