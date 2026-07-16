import { Suspense } from "react";
import { EditCandidateContent } from "@/components/forms/EditCandidateContent";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function EditCandidatePage({ params }: PageProps) {
  const { id } = await params;

  return (
    <Suspense fallback={<LoadingSpinner message="Loading..." />}>
      <EditCandidateContent id={id} />
    </Suspense>
  );
}
