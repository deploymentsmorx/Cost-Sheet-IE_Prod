import type {
  BOLineItem,
  CostingLine,
  CostSheetWithLines,
  LineOperation,
  PriceHistoryEntry,
  ProcessCostRow,
  RepriceResponse,
  SheetFinishingOp,
  Workbook,
  WorkbookSummaryOut,
} from "../types/parts"
import { API_BASE_URL } from "../lib/apiBase"

const BASE = API_BASE_URL + "/api/v1"

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? "Request failed")
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const partsApi = {
  // Workbooks
  listWorkbooks: (clientId?: number) =>
    request<Workbook[]>(clientId != null ? `/workbooks?client_id=${clientId}` : "/workbooks"),
  getSummary: (workbookId: number) =>
    request<WorkbookSummaryOut>(`/workbooks/${workbookId}/summary`),
  createWorkbook: (body: { name: string; client_id: number; description?: string; sets_count?: number }) =>
    request<Workbook>("/workbooks", { method: "POST", body: JSON.stringify(body) }),
  updateWorkbook: (id: number, body: Partial<{ name: string; client_id: number; description: string; sets_count: number }>) =>
    request<Workbook>(`/workbooks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteWorkbook: (id: number) =>
    request<void>(`/workbooks/${id}`, { method: "DELETE" }),

  // Cost Sheets (created directly under a workbook)
  listSheets: (workbookId: number) =>
    request<CostSheetWithLines[]>(`/workbooks/${workbookId}/sheets`),
  createSheet: (workbookId: number, body: {
    name: string
    part_no?: string
    description?: string
    drawing_no?: string
    benchmark_price?: string
    image_url?: string
    qty_per_set?: string
    is_optional?: boolean
    status?: string
    remarks?: string
    supply_version?: string
    discount_pct?: string
    transport_cost?: string
  }) =>
    request<CostSheetWithLines>(`/workbooks/${workbookId}/sheets`, {
      method: "POST", body: JSON.stringify(body),
    }),
  getSheet: (sheetId: number) =>
    request<CostSheetWithLines>(`/sheets/${sheetId}`),
  updateSheet: (sheetId: number, body: Partial<{
    name: string
    part_no: string | null
    description: string | null
    drawing_no: string | null
    benchmark_price: string | null
    image_url: string | null
    qty_per_set: string
    is_optional: boolean
    status: string | null
    remarks: string | null
    supply_version: string
    discount_pct: string
    transport_cost: string
  }>) =>
    request<CostSheetWithLines>(`/sheets/${sheetId}`, { method: "PATCH", body: JSON.stringify(body) }),
  saveResults: (sheetId: number) =>
    request<CostSheetWithLines>(`/sheets/${sheetId}/save-results`, { method: "POST" }),
  deleteSheet: (sheetId: number) =>
    request<void>(`/sheets/${sheetId}`, { method: "DELETE" }),
  getPriceHistory: (sheetId: number) =>
    request<PriceHistoryEntry[]>(`/sheets/${sheetId}/price-history`),
  repriceWorkbook: (workbookId: number) =>
    request<RepriceResponse>(`/workbooks/${workbookId}/reprice`, { method: "POST" }),
  uploadImage: async (sheetId: number, file: File) => {
    const form = new FormData()
    form.append("file", file)
    const res = await fetch(`${BASE}/sheets/${sheetId}/image`, { method: "POST", body: form })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail ?? "Upload failed")
    }
    return res.json() as Promise<CostSheetWithLines>
  },

  // RM Lines
  addLine: (sheetId: number, body: object & { parent_line_id?: number | null }) =>
    request<CostingLine>(`/sheets/${sheetId}/lines`, { method: "POST", body: JSON.stringify(body) }),
  updateLine: (sheetId: number, lineId: number, body: object & { parent_line_id?: number | null }) =>
    request<CostingLine>(`/sheets/${sheetId}/lines/${lineId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteLine: (sheetId: number, lineId: number) =>
    request<void>(`/sheets/${sheetId}/lines/${lineId}`, { method: "DELETE" }),

  // BO Line Items
  addBoItem: (sheetId: number, body: { description?: string; qty: string; unit_price: string }) =>
    request<BOLineItem>(`/sheets/${sheetId}/bo-items`, { method: "POST", body: JSON.stringify(body) }),
  updateBoItem: (sheetId: number, itemId: number, body: Partial<{ description: string; qty: string; unit_price: string }>) =>
    request<BOLineItem>(`/sheets/${sheetId}/bo-items/${itemId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteBoItem: (sheetId: number, itemId: number) =>
    request<void>(`/sheets/${sheetId}/bo-items/${itemId}`, { method: "DELETE" }),

  // Line Operations
  addOperation: (lineId: number, body: { operation_type: string; input_data: Record<string, unknown> }) =>
    request<LineOperation>(`/costing-lines/${lineId}/operations`, { method: "POST", body: JSON.stringify(body) }),
  updateOperation: (lineId: number, opId: number, body: Partial<{ operation_type: string; input_data: Record<string, unknown> }>) =>
    request<LineOperation>(`/costing-lines/${lineId}/operations/${opId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteOperation: (lineId: number, opId: number) =>
    request<void>(`/costing-lines/${lineId}/operations/${opId}`, { method: "DELETE" }),

  // Process Cost Rows
  updateProcessRow: (rowId: number, body: Partial<{
    equi_spec: string | null
    thk: string | null
    unit_cut_length: string | null
    use_laser: boolean
    machining_rate: string | null
    bev_slant: string | null
    bev_length: string | null
    bend_num_bends: number | null
    drill_size: string | null
    drill_hours: string | null
    drill_type: string
    has_rolling: boolean
  }>) =>
    request<ProcessCostRow>(`/process-rows/${rowId}`, { method: "PATCH", body: JSON.stringify(body) }),

  // Sheet Finishing Ops
  addFinishingOp: (sheetId: number, body: { operation_name: string; input_qty: string }) =>
    request<SheetFinishingOp>(`/sheets/${sheetId}/finishing-ops`, { method: "POST", body: JSON.stringify(body) }),
  updateFinishingOp: (sheetId: number, opId: number, body: { input_qty: string }) =>
    request<SheetFinishingOp>(`/sheets/${sheetId}/finishing-ops/${opId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteFinishingOp: (sheetId: number, opId: number) =>
    request<void>(`/sheets/${sheetId}/finishing-ops/${opId}`, { method: "DELETE" }),
}
