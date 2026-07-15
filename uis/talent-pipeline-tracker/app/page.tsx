import { Suspense } from "react";
import { CandidateListContent } from "@/components/candidates/CandidateListContent";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

export default function HomePage() {
  return (
    <Suspense fallback={<LoadingSpinner message="Loading candidates..." />}>
      <CandidateListContent />
    </Suspense>
  );
}
