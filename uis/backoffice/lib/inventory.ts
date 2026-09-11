/**
 * Inventory HTTP for the backoffice. Components must import these helpers
 * instead of calling fetch.
 *
 * Lesson env: NEXT_PUBLIC_INVENTORY_API_URL=http://localhost:8000
 * Falls back to NEXT_PUBLIC_API_BASE_URL / http://localhost:8000. Bearer via @repo/auth.
 */
import {
  authFetch,
  AuthSessionError,
  getBrasalandApiBase,
  getToken,
  messageForHttpStatus,
  parseApiError,
} from "@repo/auth";
import { clearToken } from "@repo/auth";

export type Ingredient = {
  id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  country: "CO" | "US" | string;
  current_stock: number;
};

export type IngredientSummary = {
  id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  country: string;
};

export type OrderRow = {
  type: "entry" | "exit";
  id: number;
  ingredient_id: number;
  quantity: number;
  location_id: number;
  created_at: string;
  user_uuid: string;
  ingredient: IngredientSummary;
  supplier_name?: string | null;
  reason?: string | null;
};

export type InboundCreateInput = {
  ingredient_id: number;
  quantity: number;
  supplier_name: string;
  location_id: number;
};

export type OutboundCreateInput = {
  ingredient_id: number;
  quantity: number;
  reason: "consumption" | "waste";
  location_id: number;
};

export class InventoryApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "InventoryApiError";
    this.status = status;
  }
}

const REQUEST_FALLBACK =
  "Could not complete that inventory request. Try again or contact hello@brasaland.com.";

export function getInventoryApiBase(): string {
  return (
    process.env.NEXT_PUBLIC_INVENTORY_API_URL?.replace(/\/$/, "") ||
    getBrasalandApiBase()
  );
}

async function inventoryFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const base = getInventoryApiBase();
  if (base === getBrasalandApiBase()) {
    return authFetch(path, options);
  }

  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${base}${path}`, { ...options, headers });
  } catch {
    throw new Error(
      "Could not reach the Brasaland service. Check your connection and try again.",
    );
  }

  if (response.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.assign("/login");
    }
    throw new AuthSessionError("Session expired. Please log in again.", 401);
  }

  return response;
}

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

async function throwIfNotOk(response: Response): Promise<void> {
  if (response.ok) return;
  throw new InventoryApiError(await parseError(response), response.status);
}

export async function listIngredients(): Promise<Ingredient[]> {
  const response = await inventoryFetch("/inventory/products");
  await throwIfNotOk(response);
  return (await response.json()) as Ingredient[];
}

export async function getIngredient(id: number): Promise<Ingredient> {
  const response = await inventoryFetch(`/inventory/products/${id}`);
  await throwIfNotOk(response);
  return (await response.json()) as Ingredient;
}

export async function createInbound(
  body: InboundCreateInput,
): Promise<unknown> {
  const response = await inventoryFetch("/inventory/orders/inbound", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  await throwIfNotOk(response);
  return response.json();
}

export async function createOutbound(
  body: OutboundCreateInput,
): Promise<unknown> {
  const response = await inventoryFetch("/inventory/orders/outbound", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  await throwIfNotOk(response);
  return response.json();
}

export async function listOrders(): Promise<OrderRow[]> {
  const response = await inventoryFetch("/inventory/orders");
  await throwIfNotOk(response);
  return (await response.json()) as OrderRow[];
}
