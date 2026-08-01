import type {
  NormsLookup,
  NormLibraryDetail,
  NormLibrarySummary,
  OverheadParamUpdate,
  ProcessRateUpdate,
  RmPricesBulkUpdate,
} from "../types/norms"

const BASE = "/api/v1/norms"

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const msg = body?.detail ?? `HTTP ${res.status}`
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const normsApi = {
  lookup: (clientId: number) => req<NormsLookup>(`/lookup?client_id=${clientId}`),
  listLibraries: (clientId?: number) =>
    req<NormLibrarySummary[]>(clientId != null ? `/libraries?client_id=${clientId}` : "/libraries"),
  getLibrary: (id: number) => req<NormLibraryDetail>(`/libraries/${id}`),
  createLibrary: (body: { client_id: number; label: string; seed_defaults?: boolean }) =>
    req<NormLibraryDetail>("/libraries", { method: "POST", body: JSON.stringify(body) }),
  deleteLibrary: (id: number) => req<void>(`/libraries/${id}`, { method: "DELETE" }),
  duplicate: (id: number) => req<NormLibraryDetail>(`/libraries/${id}/duplicate`, { method: "POST" }),
  publish: (id: number) => req<NormLibraryDetail>(`/libraries/${id}/publish`, { method: "POST" }),
  rename: (id: number, label: string) =>
    req<NormLibraryDetail>(`/libraries/${id}/rename`, { method: "PATCH", body: JSON.stringify({ label }) }),

  updateRmPrices: (id: number, body: RmPricesBulkUpdate) =>
    req<NormLibraryDetail>(`/libraries/${id}/rm-prices`, { method: "PATCH", body: JSON.stringify(body) }),

  addGrade: (id: number, body: { name: string; base_grade_id?: number; premium_amount?: string; initial_price?: string }) =>
    req<NormLibraryDetail>(`/libraries/${id}/grades`, { method: "POST", body: JSON.stringify(body) }),

  updateProcessRates: (id: number, rates: ProcessRateUpdate[]) =>
    req<NormLibraryDetail>(`/libraries/${id}/process-rates`, { method: "PATCH", body: JSON.stringify({ rates }) }),

  addProcessRate: (id: number, body: { operation_name: string; unit: string; rate: string; group_label: string }) =>
    req<NormLibraryDetail>(`/libraries/${id}/process-rates`, { method: "POST", body: JSON.stringify(body) }),

  updateOverheadParams: (id: number, params: OverheadParamUpdate[]) =>
    req<NormLibraryDetail>(`/libraries/${id}/overhead-params`, { method: "PATCH", body: JSON.stringify({ params }) }),

  addOverheadParam: (id: number, body: { applies_to: string; param_name: string; param_value?: string }) =>
    req<NormLibraryDetail>(`/libraries/${id}/overhead-params`, { method: "POST", body: JSON.stringify(body) }),
}
