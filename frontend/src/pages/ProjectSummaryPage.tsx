import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { ChevronRight, BarChart3, Check } from "lucide-react"
import { partsApi } from "../api/parts"
import { Button } from "../components/ui/button"
import { cn } from "../lib/utils"
import type { CostSheetSummary, RepriceResponse } from "../types/parts"

function fmt(v: string | number | null | undefined, dp = 2) {
  if (v == null || v === "") return "—"
  return Number(v).toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

function fmtDate(s: string | null | undefined) {
  if (!s) return "—"
  return new Date(s).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
}

const sub = "px-3 py-3 text-right text-xs tabular-nums"
const ic = "border border-slate-200 rounded-md px-2 py-1 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-primary/30"

const STATUS_OPTIONS = ["Approved by MD", "No supply", "No orders", "Stock on hand"]
const DEFAULT_SCENARIOS = [2, 2.49, 5]

// ---------------------------------------------------------------------------
// Editable cell helpers
// ---------------------------------------------------------------------------

interface RowEdits { qty_per_set: string; status: string; remarks: string }

export function ProjectSummaryPage() {
  const { workbookId } = useParams<{ workbookId: string }>()
  const wid = Number(workbookId)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: summary, isLoading } = useQuery({
    queryKey: ["summary", wid],
    queryFn: () => partsApi.getSummary(wid),
  })

  const [edits, setEdits] = useState<Record<number, RowEdits>>({})
  const [setsEditing, setSetsEditing] = useState(false)
  const [setsValue, setSetsValue] = useState("1")
  const [scenarios, setScenarios] = useState<number[]>(DEFAULT_SCENARIOS)
  const [customScenario, setCustomScenario] = useState("")
  const [repriceResult, setRepriceResult] = useState<RepriceResponse | null>(null)

  const repriceMutation = useMutation({
    mutationFn: () => partsApi.repriceWorkbook(wid),
    onSuccess: data => {
      qc.invalidateQueries({ queryKey: ["summary", wid] })
      setRepriceResult(data)
      toast.success(`Repriced ${data.repriced_count} sheet${data.repriced_count === 1 ? "" : "s"}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const updateSetsMutation = useMutation({
    mutationFn: (sets_count: number) => partsApi.updateWorkbook(wid, { sets_count }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["summary", wid] })
      qc.invalidateQueries({ queryKey: ["workbooks"] })
      setSetsEditing(false)
      toast.success("Sets updated")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const updateSheetMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) => partsApi.updateSheet(id, body),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ["summary", wid] })
      setEdits(prev => { const n = { ...prev }; delete n[id]; return n })
      toast.success("Saved")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  function rowValue(s: CostSheetSummary, field: keyof RowEdits): string {
    return edits[s.sheet_id]?.[field] ?? (
      field === "qty_per_set" ? s.qty_per_set : field === "status" ? (s.status ?? "") : (s.remarks ?? "")
    )
  }
  function setRowValue(s: CostSheetSummary, field: keyof RowEdits, value: string) {
    const fallback: RowEdits = { qty_per_set: s.qty_per_set, status: s.status ?? "", remarks: s.remarks ?? "" }
    setEdits(prev => ({ ...prev, [s.sheet_id]: { ...fallback, ...prev[s.sheet_id], [field]: value } }))
  }
  function saveRow(s: CostSheetSummary) {
    const e = edits[s.sheet_id]
    if (!e) return
    updateSheetMutation.mutate({
      id: s.sheet_id,
      body: { qty_per_set: e.qty_per_set, status: e.status || null, remarks: e.remarks || null },
    })
  }
  function toggleOptional(s: CostSheetSummary) {
    updateSheetMutation.mutate({ id: s.sheet_id, body: { is_optional: !s.is_optional } })
  }

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading…</div>
  )
  if (!summary) return null

  const standardSheets = summary.cost_sheets.filter(s => !s.is_optional)
  const optionalSheets = summary.cost_sheets.filter(s => s.is_optional)

  function startEditSets() {
    setSetsValue(String(summary!.sets_count))
    setSetsEditing(true)
  }

  function addCustomScenario() {
    const v = Number(customScenario)
    if (!isNaN(v) && v >= 0 && !scenarios.includes(v)) {
      setScenarios(prev => [...prev, v].sort((a, b) => a - b))
    }
    setCustomScenario("")
  }

  // Standard-scope "what if" discount scenario totals (list price → scenario discount, summed at set level)
  function scenarioTotal(pct: number): number {
    return standardSheets.reduce((sum, s) => {
      if (s.total_price == null) return sum
      const scenarioPrice = Number(s.total_price) * (1 - pct / 100) + Number(s.transport_cost)
      return sum + scenarioPrice * Number(s.qty_per_set) * summary!.sets_count
    }, 0)
  }

  function renderTable(sheets: CostSheetSummary[], emptyLabel: string) {
    if (sheets.length === 0) {
      return <p className="text-xs text-slate-400 italic px-1">{emptyLabel}</p>
    }
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
        <table className="w-full text-xs whitespace-nowrap border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500">
              {[
                "#", "Name", "Part No.", "Ver", "Qty/Set", "Weight (kg)", "RM Cost", "Unit Price", "Disc %",
                "Price Aft. Disc", "Benchmark", "Gap", "Gap %", "Bal/kg", "Fab/kg", "TackW/kg", "FullW/kg",
                "Mach/kg", "Paint/kg", "Set Total Price", "Status", "Remarks", "Optional", "Saved On", "",
              ].map((h, i) => (
                <th key={i} className="px-3 py-2.5 font-semibold text-left text-[10px] uppercase tracking-wider border-r border-slate-200 last:border-r-0">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sheets.map((s, i) => {
              const hasSaved = s.saved_count > 0
              const dirty = !!edits[s.sheet_id]
              return (
                <tr key={s.sheet_id} className="hover:bg-slate-50/60 transition-colors align-middle">
                  <td className="px-3 py-2 text-slate-400 font-mono border-r border-slate-100">{i + 1}</td>
                  <td className="px-3 py-2 font-semibold text-slate-900 border-r border-slate-100 max-w-[160px] truncate">
                    <button onClick={() => navigate(`/sheets/${s.sheet_id}`)} className="hover:text-primary hover:underline text-left">
                      {s.name}
                    </button>
                  </td>
                  <td className="px-3 py-2 text-slate-400 font-mono border-r border-slate-100">{s.part_no ?? "—"}</td>
                  <td className="px-3 py-2 text-slate-500 border-r border-slate-100">{s.supply_version}</td>
                  <td className="px-2 py-1 border-r border-slate-100">
                    <input type="number" min="0" step="1" value={rowValue(s, "qty_per_set")}
                      onChange={e => setRowValue(s, "qty_per_set", e.target.value)}
                      className={cn(ic, "w-16 text-right")} />
                  </td>
                  <td className={cn(sub, "border-r border-slate-100")}>{hasSaved && s.total_weight ? fmt(s.total_weight, 3) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>{hasSaved ? fmt(s.rm_cost) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>
                    {hasSaved ? (
                      <button onClick={() => navigate(`/sheets/${s.sheet_id}`)} className="font-semibold text-slate-900 hover:text-primary hover:underline">
                        {fmt(s.total_price)}
                      </button>
                    ) : (
                      <button onClick={() => navigate(`/sheets/${s.sheet_id}`)} className="text-slate-400 hover:text-primary hover:underline">
                        {s.line_count === 0 ? "Empty" : `${s.line_count} unsaved`}
                      </button>
                    )}
                  </td>
                  <td className={cn(sub, "border-r border-slate-100")}>{hasSaved && s.discount_pct ? fmt(s.discount_pct, 1) + "%" : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100 font-medium")}>{hasSaved ? fmt(s.price_after_discount) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>{s.benchmark_price != null ? fmt(s.benchmark_price) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100", s.price_gap != null && (Number(s.price_gap) > 0 ? "text-red-600" : "text-emerald-600"))}>
                    {s.price_gap != null ? (Number(s.price_gap) > 0 ? "+" : "") + fmt(s.price_gap) : "—"}
                  </td>
                  <td className={cn(sub, "border-r border-slate-100", s.price_gap_pct != null && (Number(s.price_gap_pct) > 0 ? "text-red-600" : "text-emerald-600"))}>
                    {s.price_gap_pct != null ? (Number(s.price_gap_pct) > 0 ? "+" : "") + fmt(s.price_gap_pct, 1) + "%" : "—"}
                  </td>
                  <td className={cn(sub, "border-r border-slate-100")}>{s.bal_margin_per_kg != null ? fmt(s.bal_margin_per_kg) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>{s.fabrication_per_kg != null ? fmt(s.fabrication_per_kg) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>{s.tack_welding_per_kg != null ? fmt(s.tack_welding_per_kg) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>{s.full_welding_per_kg != null ? fmt(s.full_welding_per_kg) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>{s.machining_per_kg != null ? fmt(s.machining_per_kg) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100")}>{s.painting_per_kg != null ? fmt(s.painting_per_kg) : "—"}</td>
                  <td className={cn(sub, "border-r border-slate-100 font-semibold")}>{s.set_total_price != null ? fmt(s.set_total_price) : "—"}</td>
                  <td className="px-2 py-1 border-r border-slate-100">
                    <input
                      list="status-options"
                      value={rowValue(s, "status")}
                      onChange={e => setRowValue(s, "status", e.target.value)}
                      className={cn(ic, "w-32")}
                      placeholder="—"
                    />
                  </td>
                  <td className="px-2 py-1 border-r border-slate-100">
                    <input
                      value={rowValue(s, "remarks")}
                      onChange={e => setRowValue(s, "remarks", e.target.value)}
                      className={cn(ic, "w-36")}
                      placeholder="—"
                    />
                  </td>
                  <td className="px-3 py-2 text-center border-r border-slate-100">
                    <input type="checkbox" checked={s.is_optional} onChange={() => toggleOptional(s)} className="accent-primary" />
                  </td>
                  <td className="px-3 py-2 text-slate-400 text-xs border-r border-slate-100">{hasSaved ? fmtDate(s.saved_at) : "—"}</td>
                  <td className="px-2 py-2">
                    {dirty && (
                      <button onClick={() => saveRow(s)} title="Save" className="text-emerald-600 hover:text-emerald-700">
                        <Check className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold">
              <td colSpan={19} className="px-3 py-2.5 text-slate-500 text-[11px] uppercase tracking-wide text-right">
                Set Total ({summary!.sets_count} {summary!.sets_count === 1 ? "Set" : "Sets"})
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums font-mono">
                {fmt(sheets.reduce((sumv, s) => sumv + Number(s.set_total_price ?? 0), 0))}
              </td>
              <td colSpan={4} />
            </tr>
          </tfoot>
        </table>
      </div>
    )
  }

  return (
    <div className="max-w-full px-6 py-8 space-y-6">
      <datalist id="status-options">
        {STATUS_OPTIONS.map(o => <option key={o} value={o} />)}
      </datalist>

      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm">
        <button onClick={() => navigate("/workbooks")} className="text-slate-500 hover:text-slate-900 transition-colors font-medium">
          Costing Workbooks
        </button>
        <ChevronRight className="w-4 h-4 text-slate-400" />
        <span className="text-slate-900 font-semibold">{summary.name}</span>
        {summary.client_name && <span className="text-slate-400 ml-0.5">— {summary.client_name}</span>}
      </nav>

      {/* Page header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Summary</h1>
          <p className="text-sm text-slate-500 mt-1">All cost sheets in this workbook</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Sets control */}
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Sets</span>
            {setsEditing ? (
              <>
                <input
                  autoFocus type="number" min="1" step="1" value={setsValue}
                  onChange={e => setSetsValue(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter") updateSetsMutation.mutate(Number(setsValue)) }}
                  className={cn(ic, "w-16")}
                />
                <button onClick={() => updateSetsMutation.mutate(Number(setsValue))} className="text-emerald-600 hover:text-emerald-700">
                  <Check className="w-4 h-4" />
                </button>
                <button onClick={() => setSetsEditing(false)} className="text-slate-400 hover:text-slate-600">✕</button>
              </>
            ) : (
              <button onClick={startEditSets} className="text-sm font-semibold text-slate-800 hover:text-primary">
                × {summary.sets_count} {summary.sets_count === 1 ? "Set" : "Sets"}
              </button>
            )}
          </div>
          <Button
            size="sm" variant="outline"
            onClick={() => repriceMutation.mutate()}
            disabled={repriceMutation.isPending || summary.cost_sheets.every(s => s.saved_count === 0)}
          >
            {repriceMutation.isPending ? "Repricing…" : "Reprice All"}
          </Button>
          <Button size="sm" variant="outline" onClick={() => navigate(`/workbooks/${wid}/sheets`)}>
            Manage Sheets
          </Button>
        </div>
      </div>

      {/* Reprice results modal */}
      {repriceResult && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={e => { if (e.target === e.currentTarget) setRepriceResult(null) }}
        >
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[80vh] flex flex-col mx-4 border border-slate-200">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
              <div>
                <h2 className="text-base font-semibold text-slate-900">Repricing Complete</h2>
                <p className="text-xs text-slate-400 mt-0.5">{repriceResult.repriced_count} open quotation(s) recalculated against current norms</p>
              </div>
              <button onClick={() => setRepriceResult(null)} className="text-slate-400 hover:text-slate-700 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 text-lg leading-none">✕</button>
            </div>
            <div className="overflow-y-auto px-6 py-4">
              {repriceResult.items.length === 0 ? (
                <p className="text-sm text-slate-400 italic py-6 text-center">No open quotations to reprice — save a sheet's results first.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-slate-400 uppercase tracking-wide">
                      <th className="py-2 font-semibold">Sheet</th>
                      <th className="py-2 font-semibold text-right">Before</th>
                      <th className="py-2 font-semibold text-right">After</th>
                      <th className="py-2 font-semibold text-right">Δ%</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {repriceResult.items.map(item => (
                      <tr key={item.sheet_id}>
                        <td className="py-2 font-medium text-slate-800">{item.name}</td>
                        <td className="py-2 text-right font-mono tabular-nums text-slate-500">₹{fmt(item.before_price)}</td>
                        <td className="py-2 text-right font-mono tabular-nums font-semibold text-slate-900">₹{fmt(item.after_price)}</td>
                        <td className={cn(
                          "py-2 text-right font-mono tabular-nums font-semibold",
                          item.pct_change == null ? "text-slate-400" : Number(item.pct_change) > 0 ? "text-red-600" : "text-emerald-600"
                        )}>
                          {item.pct_change == null ? "—" : (Number(item.pct_change) > 0 ? "+" : "") + fmt(item.pct_change, 2) + "%"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {summary.cost_sheets.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
            <BarChart3 className="w-7 h-7 text-slate-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 mb-1">No cost sheets yet</h3>
          <p className="text-sm text-slate-500 mb-5">Add cost sheets to this workbook to see the summary</p>
          <Button size="sm" onClick={() => navigate(`/workbooks/${wid}/sheets`)}>
            Add Cost Sheet
          </Button>
        </div>
      ) : (
        <>
          {/* Discount scenario comparison */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-1">Discount Scenario Comparison</h2>
            <p className="text-xs text-slate-500 mb-4">
              Standard-scope set total if every sheet's list price took this discount instead of its own saved discount %.
            </p>
            <div className="flex flex-wrap items-end gap-4">
              {scenarios.map(pct => (
                <div key={pct} className="rounded-lg border border-slate-200 bg-slate-50/60 px-4 py-3 min-w-[140px] relative group">
                  <button
                    onClick={() => setScenarios(prev => prev.filter(p => p !== pct))}
                    className="absolute top-1 right-1.5 text-slate-300 hover:text-red-500 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  >✕</button>
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{pct}% Discount</p>
                  <p className="text-sm font-bold text-slate-900 font-mono mt-1">₹{fmt(scenarioTotal(pct))}</p>
                </div>
              ))}
              <div className="flex items-end gap-1.5 pb-0.5">
                <input
                  type="number" min="0" step="0.01" placeholder="Custom %"
                  value={customScenario}
                  onChange={e => setCustomScenario(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter") addCustomScenario() }}
                  className={cn(ic, "w-24")}
                />
                <Button size="sm" variant="outline" onClick={addCustomScenario} disabled={!customScenario}>+ Add</Button>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 px-4 py-3 min-w-[140px] ml-auto">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700">Actual (Saved Discounts)</p>
                <p className="text-sm font-bold text-emerald-900 font-mono mt-1">₹{fmt(summary.standard_total_price)}</p>
              </div>
            </div>
          </div>

          {/* Standard scope */}
          <section className="space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Standard Scope</h2>
            {renderTable(standardSheets, "No standard-scope sheets.")}
          </section>

          {/* Optional items */}
          <section className="space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Optional Items</h2>
            {renderTable(optionalSheets, "No optional items — check the \"Optional\" box on a sheet to move it here.")}
          </section>

          {/* Grand summary */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-3">Project Totals</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-xs">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1">Standard Total</p>
                <p className="font-mono font-bold text-slate-900">₹{fmt(summary.standard_total_price)}</p>
                <p className="text-slate-400 mt-0.5">{fmt(summary.standard_total_weight, 3)} kg</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1">Optional Total</p>
                <p className="font-mono font-bold text-slate-900">₹{fmt(summary.optional_total_price)}</p>
                <p className="text-slate-400 mt-0.5">{fmt(summary.optional_total_weight, 3)} kg</p>
              </div>
              {summary.benchmark_total != null && (
                <>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1">Benchmark Total (Std.)</p>
                    <p className="font-mono font-bold text-slate-900">₹{fmt(summary.benchmark_total)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1">Gap vs Benchmark</p>
                    <p className={cn("font-mono font-bold", Number(summary.benchmark_gap_total) > 0 ? "text-red-600" : "text-emerald-600")}>
                      {Number(summary.benchmark_gap_total) > 0 ? "+" : ""}₹{fmt(summary.benchmark_gap_total)}
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </>
      )}

      <p className="text-xs text-slate-400">
        Click any sheet name or unit price to open the cost sheet editor. Qty/Set, Status and Remarks save with the checkmark that appears after editing.
      </p>
    </div>
  )
}
