import dynamic from "next/dynamic";
import { BackofficeShell } from "@/components/BackofficeShell";

const OutboundExitForm = dynamic(
  () =>
    import("@/components/inventory/OutboundExitForm").then(
      (mod) => mod.OutboundExitForm,
    ),
  {
    loading: () => <p role="status">Loading the consumption and waste form…</p>,
  },
);

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
