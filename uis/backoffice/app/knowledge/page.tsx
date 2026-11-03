import { BackofficeShell } from "@/components/BackofficeShell";
import { KnowledgeQuery } from "@/components/KnowledgeQuery";

export const dynamic = "force-dynamic";

export default function KnowledgePage() {
  return (
    <BackofficeShell>
      <KnowledgeQuery />
    </BackofficeShell>
  );
}
