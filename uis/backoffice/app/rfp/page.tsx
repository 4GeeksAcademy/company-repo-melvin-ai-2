import { BackofficeShell } from "@/components/BackofficeShell";
import { RfpIntake } from "@/components/RfpIntake";

export const dynamic = "force-dynamic";

export default function RfpPage() {
  return (
    <BackofficeShell>
      <RfpIntake />
    </BackofficeShell>
  );
}
