import { BackofficeShell } from "@/components/BackofficeShell";
import { OutboundExitForm } from "@/components/inventory/OutboundExitForm";

type PageProps = {
  searchParams: Promise<{ ingredient_id?: string }>;
};

function parseIngredientId(raw: string | undefined): number | undefined {
  if (!raw) return undefined;
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : undefined;
}

export default async function OutboundPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return (
    <BackofficeShell>
      <OutboundExitForm
        initialIngredientId={parseIngredientId(params.ingredient_id)}
      />
    </BackofficeShell>
  );
}
