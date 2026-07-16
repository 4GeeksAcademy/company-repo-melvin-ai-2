import { Suspense } from "react";
import { NewCandidateContent } from "@/components/forms/NewCandidateContent";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

export default function NewCandidatePage() {
  return (
    <Suspense fallback={<LoadingSpinner message="Loading..." />}>
      <NewCandidateContent />
    </Suspense>
  );
}
