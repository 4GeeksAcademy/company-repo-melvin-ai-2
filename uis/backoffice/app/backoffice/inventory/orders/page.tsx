import { BackofficeShell } from "@/components/BackofficeShell";
import { OrdersHistory } from "@/components/inventory/OrdersHistory";

export default function InventoryOrdersPage() {
  return (
    <BackofficeShell>
      <OrdersHistory />
    </BackofficeShell>
  );
}
