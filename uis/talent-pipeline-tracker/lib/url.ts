export function buildListQueryString(params: {
  status?: string;
  stage?: string;
  search?: string;
  page?: string;
}): string {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set("status", params.status);
  if (params.stage) searchParams.set("stage", params.stage);
  if (params.search) searchParams.set("search", params.search);
  if (params.page && params.page !== "1") searchParams.set("page", params.page);
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function buildReturnTo(params: {
  status?: string;
  stage?: string;
  search?: string;
  page?: string;
}): string {
  return encodeURIComponent(`/${buildListQueryString(params)}`);
}
