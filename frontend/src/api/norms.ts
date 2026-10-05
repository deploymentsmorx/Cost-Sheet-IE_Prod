import type {
  NormsLookup,
  NormLibraryDetail,
  NormLibrarySummary,
  OverheadParamUpdate,
  ProcessRateUpdate,
  RmPricesBulkUpdate,
  RmPriceTrendPoint,
  SectionCategory,
} from "../types/norms"
import { API_BASE_URL } from "../lib/apiBase"

const BASE = API_BASE_URL + "/api/v1/norms"

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
  rmPriceTrend: (clientId: number, gradeId: number, thicknessBand: string) =>
    req<RmPriceTrendPoint[]>(`/rm-price-trend?client_id=${clientId}&grade_id=${gradeId}&thickness_band=${encodeURIComponent(thicknessBand)}`),
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

  // Steel price build-up
  addSteelBuildup: (id: number, body: { grade_id: number; thickness_band: string; basic_price_per_tonne: string; ust_amount?: string; trimming_amount?: string; normalising_amount?: string; trader_transport_constant?: string }) =>
    req<NormLibraryDetail>(`/libraries/${id}/steel-buildups`, { method: "POST", body: JSON.stringify(body) }),
  updateSteelBuildup: (id: number, buildupId: number, body: Partial<{ basic_price_per_tonne: string; ust_amount: string; trimming_amount: string; normalising_amount: string; trader_transport_constant: string }>) =>
    req<NormLibraryDetail>(`/libraries/${id}/steel-buildups/${buildupId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteSteelBuildup: (id: number, buildupId: number) =>
    req<NormLibraryDetail>(`/libraries/${id}/steel-buildups/${buildupId}`, { method: "DELETE" }),
  applySteelBuildupToRm: (id: number, buildupId: number) =>
    req<NormLibraryDetail>(`/libraries/${id}/steel-buildups/${buildupId}/apply-to-rm`, { method: "POST" }),

  // Grade equivalence
  addGradeEquivalence: (id: number, body: { customer_spec: string; material_grade_id: number; notes?: string }) =>
    req<NormLibraryDetail>(`/libraries/${id}/grade-equivalences`, { method: "POST", body: JSON.stringify(body) }),
  updateGradeEquivalence: (id: number, equivId: number, body: Partial<{ customer_spec: string; material_grade_id: number; notes: string }>) =>
    req<NormLibraryDetail>(`/libraries/${id}/grade-equivalences/${equivId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteGradeEquivalence: (id: number, equivId: number) =>
    req<NormLibraryDetail>(`/libraries/${id}/grade-equivalences/${equivId}`, { method: "DELETE" }),
  resolveGradeEquivalence: (clientId: number, spec: string) =>
    req<{ customer_spec: string; material_grade_id: number; material_grade_name: string }>(
      `/grade-equivalences/resolve?client_id=${clientId}&spec=${encodeURIComponent(spec)}`
    ),

  // Section / bar / tube catalogue
  addSectionCatalogItem: (id: number, body: { category: SectionCategory; designation: string; kg_per_m: string; rate_per_kg: string }) =>
    req<NormLibraryDetail>(`/libraries/${id}/section-catalog`, { method: "POST", body: JSON.stringify(body) }),
  updateSectionCatalogItem: (id: number, itemId: number, body: Partial<{ category: SectionCategory; designation: string; kg_per_m: string; rate_per_kg: string }>) =>
    req<NormLibraryDetail>(`/libraries/${id}/section-catalog/${itemId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteSectionCatalogItem: (id: number, itemId: number) =>
    req<NormLibraryDetail>(`/libraries/${id}/section-catalog/${itemId}`, { method: "DELETE" }),

  // Bought-out item master
  addBoCatalogItem: (id: number, body: { name: string; category?: string; unit_weight_kg?: string; rate: string }) =>
    req<NormLibraryDetail>(`/libraries/${id}/bo-catalog`, { method: "POST", body: JSON.stringify(body) }),
  updateBoCatalogItem: (id: number, itemId: number, body: Partial<{ name: string; category: string; unit_weight_kg: string; rate: string }>) =>
    req<NormLibraryDetail>(`/libraries/${id}/bo-catalog/${itemId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteBoCatalogItem: (id: number, itemId: number) =>
    req<NormLibraryDetail>(`/libraries/${id}/bo-catalog/${itemId}`, { method: "DELETE" }),
}
