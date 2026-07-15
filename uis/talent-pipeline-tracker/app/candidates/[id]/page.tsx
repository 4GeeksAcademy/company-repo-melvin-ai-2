import { Suspense } from "react";
import { CandidateDetailContent } from "@/components/detail/CandidateDetailContent";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function CandidateDetailPage({ params }: PageProps) {
  const { id } = await params;

  return (
    <Suspense fallback={<LoadingSpinner message="Loading candidate..." />}>
      <CandidateDetailContent id={id} />
    </Suspense>
  );
}
