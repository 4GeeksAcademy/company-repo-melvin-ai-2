import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { VisitNotice } from "@/components/VisitNotice";

const LoyaltyForm = dynamic(
  () => import("@/components/LoyaltyForm").then((mod) => mod.LoyaltyForm),
  {
    loading: () => (
      <p role="status">Loading the Brasa Points registration form…</p>
    ),
  },
);

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
            <VisitNotice />
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
