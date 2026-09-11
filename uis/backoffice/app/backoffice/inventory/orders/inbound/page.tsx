import { BackofficeShell } from "@/components/BackofficeShell";
import { InboundDeliveryForm } from "@/components/inventory/InboundDeliveryForm";

type PageProps = {
  searchParams: Promise<{ ingredient_id?: string }>;
};

function parseIngredientId(raw: string | undefined): number | undefined {
  if (!raw) return undefined;
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : undefined;
}

export default async function InboundPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return (
    <BackofficeShell>
      <InboundDeliveryForm
        initialIngredientId={parseIngredientId(params.ingredient_id)}
      />
    </BackofficeShell>
  );
}
