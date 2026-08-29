import { authFetch, messageForHttpStatus, parseApiError } from "@repo/auth";

export type Supplier = {
  id: number;
  name: string;
  country: "Colombia" | "USA";
  categories: string[];
  rate_per_unit: number;
  currency: "COP" | "USD";
  status: "active" | "suspended";
  updated_at: string | null;
  contact_email?: string | null;
  notes?: string | null;
};

export type SupplierCreateInput = {
  name: string;
  country: "Colombia" | "USA";
  categories: string[];
  rate_per_unit: number;
  currency: "COP" | "USD";
  status: "active" | "suspended";
  contact_email?: string;
  notes?: string;
};

const REQUEST_FALLBACK =
  "Could not complete that supplier request. Try again or contact hello@brasaland.com.";

async function parseError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as unknown;
    return parseApiError(
      payload,
      messageForHttpStatus(response.status, REQUEST_FALLBACK),
    );
  } catch {
    return messageForHttpStatus(response.status, REQUEST_FALLBACK);
  }
}

export async function listSuppliers(filters?: {
  country?: string;
  category?: string;
}): Promise<Supplier[]> {
  const params = new URLSearchParams();
  if (filters?.country) params.set("country", filters.country);
  if (filters?.category) params.set("category", filters.category);
  const suffix = params.toString() ? `?${params}` : "";
  const response = await authFetch(`/suppliers${suffix}`);
  if (!response.ok) throw new Error(await parseError(response));
  return (await response.json()) as Supplier[];
}

export async function createSupplier(
  body: SupplierCreateInput,
): Promise<Supplier> {
  const response = await authFetch(`/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return (await response.json()) as Supplier;
}

export async function updateSupplierRate(
  id: number,
  rate_per_unit: number,
): Promise<Supplier> {
  const response = await authFetch(`/suppliers/${id}/rate`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rate_per_unit }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return (await response.json()) as Supplier;
}

export async function updateSupplierStatus(
  id: number,
  status: "active" | "suspended",
): Promise<Supplier> {
  const response = await authFetch(`/suppliers/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return (await response.json()) as Supplier;
}

export const VALID_CATEGORIES = [
  "carne",
  "verduras_y_hortalizas",
  "salsas_y_condimentos",
  "bebidas",
  "packaging",
  "productos_limpieza",
  "lacteos",
  "carbon_y_combustible",
] as const;
