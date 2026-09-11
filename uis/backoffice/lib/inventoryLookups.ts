/** 14 Brasaland kitchens. Values are location_id 1–14 sent to the inventory API. */
export const BRASALAND_LOCATIONS: { id: number; label: string }[] = [
  { id: 1, label: "Medellín Centro" },
  { id: 2, label: "Medellín El Poblado" },
  { id: 3, label: "Medellín Laureles" },
  { id: 4, label: "Medellín Envigado" },
  { id: 5, label: "Bogotá Chapinero" },
  { id: 6, label: "Bogotá Zona T" },
  { id: 7, label: "Bogotá Usaquén" },
  { id: 8, label: "Cali Granada" },
  { id: 9, label: "Cali Ciudad Jardín" },
  { id: 10, label: "Cali Norte" },
  { id: 11, label: "Miami Beach" },
  { id: 12, label: "Miami Brickell" },
  { id: 13, label: "Orlando International Drive" },
  { id: 14, label: "Orlando Downtown" },
];

export const DELIVERY_SUPPLIERS = [
  "Carnes del Valle S.A.",
  "MiamiMeat Co.",
  "Salsas Artesanales Ltda.",
] as const;

export const OTHER_SUPPLIER = "__other__";

export function locationLabel(id: number): string {
  return BRASALAND_LOCATIONS.find((row) => row.id === id)?.label ?? `Location ${id}`;
}

export function countryLabel(code: string): string {
  if (code === "CO") return "Colombia";
  if (code === "US") return "United States";
  return code;
}

export function formatQuantity(value: number, unit: string): string {
  const rounded = Math.round(value * 100) / 100;
  const text = Number.isInteger(rounded)
    ? String(rounded)
    : rounded.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
  return `${text} ${unit}`;
}

export function formatOrderWhen(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Bogota",
  }).format(date);
}
