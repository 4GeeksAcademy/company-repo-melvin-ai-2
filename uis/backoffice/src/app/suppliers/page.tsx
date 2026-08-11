import { BackofficeShell } from "@/components/BackofficeShell";
import { SupplierDirectory } from "@/components/SupplierDirectory";

export default function SuppliersPage() {
  return (
    <BackofficeShell>
      <SupplierDirectory />
    </BackofficeShell>
  );
}
