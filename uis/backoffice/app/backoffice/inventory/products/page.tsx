import { BackofficeShell } from "@/components/BackofficeShell";
import { IngredientsList } from "@/components/inventory/IngredientsList";

export default function InventoryProductsPage() {
  return (
    <BackofficeShell>
      <IngredientsList />
    </BackofficeShell>
  );
}
