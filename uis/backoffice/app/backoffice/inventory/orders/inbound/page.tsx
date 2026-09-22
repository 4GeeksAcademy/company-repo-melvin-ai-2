import dynamic from "next/dynamic";
import { BackofficeShell } from "@/components/BackofficeShell";

const InboundDeliveryForm = dynamic(
  () =>
    import("@/components/inventory/InboundDeliveryForm").then(
      (mod) => mod.InboundDeliveryForm,
    ),
  {
    loading: () => <p role="status">Loading the delivery form…</p>,
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
