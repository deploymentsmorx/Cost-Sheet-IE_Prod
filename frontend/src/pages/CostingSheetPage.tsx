import { Fragment, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { useNavigate, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { ChevronRight, LayoutList } from "lucide-react"
import { partsApi } from "../api/parts"
import { normsApi } from "../api/norms"
import { LineEditorPanel } from "../components/costing/LineEditorPanel"
import { FormulasModal } from "../components/costing/FormulasModal"
import { ProcessCostSection } from "../components/costing/ProcessCostSection"
import { AiInsightsPanel } from "../components/costing/AiInsightsPanel"
import { CostBreakdownDonut } from "../components/charts/CostBreakdownDonut"
import { Button } from "../components/ui/button"
import { cn } from "../lib/utils"
import type { CostingLine, BlockMarkup, RmLineResult } from "../types/parts"

function n(v: string | number | undefined | null, dp = 2) {
  if (v == null || v === "") return "—"
  return Number(v).toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

// ---------------------------------------------------------------------------
// Shared small components
// ---------------------------------------------------------------------------

function SectionHead({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-[11px] font-bold uppercase tracking-widest text-slate-400">{children}</span>
      <div className="flex-1 h-px bg-slate-100" />
    </div>
  )
}

function BlockCard({ title, block, accent }: { title: string; block: BlockMarkup; accent: string }) {
  return (
    <div className={cn("rounded-xl border p-4 min-w-[168px] flex-1", accent)}>
      <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-500">{title}</p>
      <div className="space-y-1 text-xs">
        <BlockRow label="Base Total" value={block.base_total} />
        <BlockRow label="Overhead"   value={block.overhead} />
        {Number(block.rework)    > 0 && <BlockRow label="Rework"    value={block.rework} />}
        {Number(block.inventory) > 0 && <BlockRow label="Inventory" value={block.inventory} />}
        <BlockRow label="Profit"     value={block.profit} />
        <div className="border-t border-slate-200/80 mt-1.5 pt-1.5">
          <BlockRow label="Grand Total" value={block.grand_total} bold />
        </div>
      </div>
    </div>
  )
}

function BlockRow({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className={cn("flex justify-between gap-2", bold && "font-semibold")}>
      <span className={bold ? "text-slate-700" : "text-slate-500"}>{label}</span>
      <span className="tabular-nums font-mono text-slate-800">₹{n(value)}</span>
    </div>
  )
}

function RmRow({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <tr className={bold ? "font-semibold border-t border-slate-200" : ""}>
      <td className="py-1 pr-4 text-slate-500 text-xs">{label}</td>
      <td className="py-1 text-right font-mono tabular-nums text-xs text-slate-800">{value}</td>
    </tr>
  )
}

// ---------------------------------------------------------------------------
// RM chain hover tooltip (portal so it's never clipped by table overflow)
// ---------------------------------------------------------------------------

function RmChainTooltip({ rm, noNorms, children }: {
  rm: RmLineResult | null
  noNorms: boolean
  children: React.ReactNode
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)

  function show() {
    if (ref.current) {
      const r = ref.current.getBoundingClientRect()
      setPos({ x: r.left + r.width / 2, y: r.top - 8 })
    }
  }

  const tooltip = pos && createPortal(
    <div
      style={{ position: "fixed", left: pos.x, top: pos.y, transform: "translate(-50%, -100%)", zIndex: 9999 }}
      className="bg-slate-900 text-white rounded-lg shadow-2xl p-3 w-52 pointer-events-none"
    >
      {rm ? (
        <>
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">RM Chain</p>
          <div className="space-y-1">
            {([
              ["Part Wt / pc",   `${n(rm.part_weight, 3)} kg`],
              ["Blank Wt / pc",  `${n(rm.blank_weight, 3)} kg`],
              ["Total Part Wt",  `${n(rm.total_part_weight, 3)} kg`],
              ["Total Blank Wt", `${n(rm.total_blank_weight, 3)} kg`],
              ["Blank Rate",     `₹${n(rm.blank_rate, 4)}/kg`],
              ["Blank Cost",     `₹${n(rm.blank_cost)}`],
              [`Proc Loss (${n(rm.process_loss_pct, 0)}%)`, `${n(rm.process_loss_weight, 3)} kg`],
              ["Scrap Credit",   `₹${n(rm.scrap_cost)}`],
            ] as [string, string][]).map(([label, val]) => (
              <div key={label} className="flex justify-between text-xs">
                <span className="text-slate-400">{label}</span>
                <span className="font-mono tabular-nums">{val}</span>
              </div>
            ))}
            <div className="border-t border-slate-700 mt-1 pt-1 flex justify-between text-xs font-semibold">
              <span className="text-slate-200">RM Cost</span>
              <span className="font-mono text-amber-400">₹{n(rm.rm_cost)}</span>
            </div>
          </div>
        </>
      ) : (
        <p className="text-xs text-slate-300">
          {noNorms
            ? "No published norm library — publish one from the Norms Library page."
            : "RM price not set for this grade / thickness band."}
        </p>
      )}
      <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900" />
    </div>,
    document.body
  )

  return (
    <>
      <span
        ref={ref}
        className="cursor-help"
        onMouseEnter={show}
        onMouseLeave={() => setPos(null)}
      >
        {children}
      </span>
      {tooltip}
    </>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

const RM_COLS = 12

export function CostingSheetPage() {
  const { sheetId } = useParams<{ sheetId: string }>()
  const id = Number(sheetId)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: sheet, isLoading } = useQuery({
    queryKey: ["sheet", id],
    queryFn: () => partsApi.getSheet(id),
  })

  const clientId = sheet?.client_id ?? null

  const { data: normsLookup } = useQuery({
    queryKey: ["norms-lookup", clientId],
    queryFn: () => normsApi.lookup(clientId!),
    staleTime: 60_000,
    enabled: clientId != null,
  })

  const gradeMap: Record<number, string> = Object.fromEntries(
    (normsLookup?.material_grades ?? []).map(g => [g.id, g.name])
  )
  const processRateNames = (normsLookup?.process_rates ?? []).map(pr => pr.operation_name)

  // RM line editor state
  const [editorOpen, setEditorOpen] = useState(false)
  const [editingLine, setEditingLine] = useState<CostingLine | null>(null)
  const [expandedLineId, setExpandedLineId] = useState<number | null>(null)

  // BO form
  const [boFormOpen, setBoFormOpen] = useState(false)
  const [boForm, setBoForm] = useState({ description: "", qty: "1", unit_price: "0" })

  // Finishing op form
  const [finFormOpen, setFinFormOpen] = useState(false)
  const [finForm, setFinForm] = useState({ operation_name: "", input_qty: "0" })

  // Sheet settings
  const [settingsEditing, setSettingsEditing] = useState(false)
  const [settingsForm, setSettingsForm] = useState({ discount_pct: "0", transport_cost: "0" })

  // ─── Mutations ───────────────────────────────────────────────────────────

  const deleteLineMutation = useMutation({
    mutationFn: ({ lineId }: { lineId: number }) => partsApi.deleteLine(id, lineId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheet", id] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      toast.success("Line deleted")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const saveMutation = useMutation({
    mutationFn: () => partsApi.saveResults(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheet", id] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      toast.success("Results saved")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const addBoMutation = useMutation({
    mutationFn: () => partsApi.addBoItem(id, {
      description: boForm.description || undefined,
      qty: boForm.qty,
      unit_price: boForm.unit_price,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheet", id] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      toast.success("BO item added")
      setBoFormOpen(false)
      setBoForm({ description: "", qty: "1", unit_price: "0" })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteBoMutation = useMutation({
    mutationFn: ({ itemId }: { itemId: number }) => partsApi.deleteBoItem(id, itemId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheet", id] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      toast.success("BO item removed")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const addFinMutation = useMutation({
    mutationFn: () => partsApi.addFinishingOp(id, {
      operation_name: finForm.operation_name,
      input_qty: finForm.input_qty,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheet", id] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      toast.success("Finishing op added")
      setFinFormOpen(false)
      setFinForm({ operation_name: "", input_qty: "0" })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteFinMutation = useMutation({
    mutationFn: ({ opId }: { opId: number }) => partsApi.deleteFinishingOp(id, opId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheet", id] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      toast.success("Finishing op removed")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const updateSheetMutation = useMutation({
    mutationFn: () => partsApi.updateSheet(id, {
      discount_pct: settingsForm.discount_pct,
      transport_cost: settingsForm.transport_cost,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheet", id] })
      qc.invalidateQueries({ queryKey: ["summary"] })
      toast.success("Sheet updated")
      setSettingsEditing(false)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  // ─── Handlers ────────────────────────────────────────────────────────────

  function openNew() { setEditingLine(null); setEditorOpen(true) }
  function openEdit(line: CostingLine) { setEditingLine(line); setEditorOpen(true) }

  function onSaved() {
    qc.invalidateQueries({ queryKey: ["sheet", id] })
    qc.invalidateQueries({ queryKey: ["summary"] })
    setEditorOpen(false)
    toast.success(editingLine ? "Line updated" : "Line added")
    setEditingLine(null)
  }

  function startEditSettings() {
    setSettingsForm({ discount_pct: sheet?.discount_pct ?? "0", transport_cost: sheet?.transport_cost ?? "0" })
    setSettingsEditing(true)
  }

  // ─── Loading ─────────────────────────────────────────────────────────────

  if (isLoading || !sheet) return (
    <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading…</div>
  )

  const lines = sheet.lines
  const boItems = sheet.bo_items
  const finOps = sheet.finishing_ops
  const sr = sheet.sheet_result

  // Live process block — mirrors previewCost() from ProcessCostSection, never uses stale DB values
  const procRateMap = Object.fromEntries((normsLookup?.process_rates ?? []).map(pr => [pr.operation_name, pr]))
  function calcOpCost(unit: string, inputs: Record<string, unknown>, rate: number, thickMm: number, qty: number, totalWt: number): number {
    const inp = (k: string) => Number(inputs[k] ?? 0)
    if (unit === "Rs/mm/meter")    return (inp("length_mm") / 1000) * thickMm * qty * rate
    if (unit === "Rs/slant/meter") return (inp("slant_length_mm") / 1000) * (inp("num_slants") || 1) * rate * qty
    if (unit === "Rs/Kg")          return totalWt * rate
    if (unit === "Rs/Hr")          return inp("hours") * qty * rate
    if (unit === "Rs/Nos" || unit === "Rs/Sqm") return inp("input_qty") * rate
    return 0
  }
  const totalProcLive =
    lines.reduce((s, ln) => {
      const thickMm = Number(ln.thickness_mm ?? 0)
      const qty     = Number(ln.qty)
      const totalWt = Number(ln.part_weight) * qty
      const lineCost = ln.operations.reduce((os, op) => {
        const pr = procRateMap[op.operation_type]
        if (!pr) return os
        return os + calcOpCost(pr.unit, op.input_data, Number(pr.rate), thickMm, qty, totalWt)
      }, 0)
      return s + lineCost
    }, 0) +
    finOps.reduce((s, fop) => s + Number(fop.computed_cost ?? 0), 0)
  const procParams = (normsLookup?.overhead_params ?? []).filter(p => p.applies_to === "process_cost")
  const getProcPct = (name: string) => {
    const p = procParams.find(p => p.param_name === name)
    return p?.param_value ? Number(p.param_value) / 100 : 0
  }
  const procOverhead = totalProcLive * getProcPct("Overhead")
  const procRework   = totalProcLive * getProcPct("Rework")
  const procProfit   = totalProcLive * getProcPct("Profit")
  const liveProcessBlock: BlockMarkup = {
    base_total:  String(totalProcLive),
    overhead:    String(procOverhead),
    rework:      String(procRework),
    inventory:   "0",
    profit:      String(procProfit),
    grand_total: String(totalProcLive + procOverhead + procRework + procProfit),
  }

  const ic = "border border-slate-200 rounded-md px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-primary/30"

  const noNormLibrary = normsLookup !== undefined && normsLookup.norm_library_id === null

  return (
    <div className="max-w-full px-6 py-8 space-y-7">

      {/* ── No norm library warning ── */}
      {noNormLibrary && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-start gap-3">
          <span className="text-amber-500 text-base mt-0.5">⚠</span>
          <div>
            <p className="text-sm font-semibold text-amber-900">No published norm library for this client</p>
            <p className="text-xs text-amber-700 mt-0.5">
              RM prices and process rates won't be calculated. Go to <strong>Norms Library</strong>, select a draft library, and click <strong>Publish Version</strong>.
            </p>
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav className="flex items-center gap-1.5 text-sm">
          <button onClick={() => navigate("/workbooks")} className="text-slate-500 hover:text-slate-900 transition-colors font-medium">
            Costing Workbooks
          </button>
          <ChevronRight className="w-4 h-4 text-slate-400" />
          <button onClick={() => navigate(-1)} className="text-slate-500 hover:text-slate-900 transition-colors font-medium">
            Costsheets
          </button>
          <ChevronRight className="w-4 h-4 text-slate-400" />
          <span className="text-slate-900 font-semibold">{sheet.supply_version}</span>
        </nav>
        <div className="flex gap-2">
          <FormulasModal />
          <Button
            size="sm" variant="outline"
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || lines.length === 0}
          >
            {saveMutation.isPending ? "Saving…" : "Save Sheet"}
          </Button>
          <Button size="sm" onClick={openNew}>+ Add Line</Button>
        </div>
      </div>

      {/* ── Line editor ── */}
      {editorOpen && (
        <LineEditorPanel
          sheetId={id}
          clientId={clientId}
          editing={editingLine}
          onSaved={onSaved}
          onCancel={() => { setEditorOpen(false); setEditingLine(null) }}
        />
      )}

      {/* ── RM Cost ── */}
      <section>
        <SectionHead>RM Cost</SectionHead>
        {lines.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
              <LayoutList className="w-7 h-7 text-slate-400" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900 mb-1">No lines yet</h3>
            <p className="text-sm text-slate-500 mb-5">Add a costing line to start calculating</p>
            <Button size="sm" onClick={openNew}>+ Add Line</Button>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
            <table className="w-full text-xs whitespace-nowrap">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500">
                  {(["Sl","Description","Spec","Grade","Band","Qty","Part Wt","Blank Wt","RM Cost","Proc Cost","Status",""] as const).map((h, i) => (
                    <th
                      key={i}
                      className={cn(
                        "px-3 py-3 font-semibold uppercase tracking-wider text-[11px]",
                        i >= 5 && i <= 9 ? "text-right" : i === 10 ? "text-center" : "text-left"
                      )}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lines.map(line => {
                  const rm = line.rm_result
                  const isExpanded = expandedLineId === line.id
                  return (
                    <Fragment key={line.id}>
                      <tr className={cn(
                        "hover:bg-slate-50/60 transition-colors align-middle",
                        editingLine?.id === line.id && "ring-1 ring-inset ring-primary/30 bg-sky-50/20",
                        isExpanded && "bg-sky-50/20"
                      )}>
                        <td className="px-3 py-3 text-slate-400 font-mono">{line.sl_no}</td>
                        <td className="px-3 py-3 font-medium text-slate-900 max-w-[160px] truncate">{line.description ?? "—"}</td>
                        <td className="px-3 py-3 text-slate-400 max-w-[100px] truncate">{line.spec ?? "—"}</td>
                        <td className="px-3 py-3 text-slate-500">
                          {line.grade_id ? (gradeMap[line.grade_id] ?? `#${line.grade_id}`) : "—"}
                        </td>
                        <td className="px-3 py-3 text-slate-500">{line.thickness_band ?? "—"}</td>
                        <td className="px-3 py-3 text-right tabular-nums">{n(line.qty, 0)}</td>
                        <td className="px-3 py-3 text-right tabular-nums font-mono">{n(line.part_weight, 3)}</td>
                        <td className="px-3 py-3 text-right tabular-nums font-mono">
                          <RmChainTooltip rm={rm} noNorms={noNormLibrary}>
                            {rm ? (
                              <button
                                onClick={() => setExpandedLineId(p => p === line.id ? null : line.id)}
                                className="underline decoration-dashed underline-offset-2 hover:text-primary"
                              >
                                {n(rm.total_blank_weight, 3)}
                              </button>
                            ) : <span className="text-slate-300">—</span>}
                          </RmChainTooltip>
                        </td>
                        <td className="px-3 py-3 text-right tabular-nums font-mono text-amber-700">
                          <RmChainTooltip rm={rm} noNorms={noNormLibrary}>
                            {rm ? n(rm.rm_cost) : <span className="text-slate-300">—</span>}
                          </RmChainTooltip>
                        </td>
                        <td className="px-3 py-3 text-right tabular-nums font-mono text-violet-700">
                          {line.line_process_cost ? n(line.line_process_cost) : "—"}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {line.saved_at ? (
                            <span className="inline-flex items-center gap-1 text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full px-2 py-0.5 font-medium">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                              Saved
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] bg-slate-50 text-slate-400 border border-slate-200 rounded-full px-2 py-0.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-slate-300 inline-block" />
                              Draft
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex items-center gap-0.5">
                            <button
                              onClick={() => setExpandedLineId(p => p === line.id ? null : line.id)}
                              className="text-xs font-medium text-slate-500 hover:text-primary hover:bg-sky-50 px-2 py-1 rounded-md transition-colors"
                            >
                              {isExpanded ? "Close" : "Detail"}
                            </button>
                            <button
                              onClick={() => openEdit(line)}
                              className="text-xs font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-100 px-2 py-1 rounded-md transition-colors"
                            >Edit</button>
                            <button
                              onClick={() => { if (confirm("Delete this line?")) deleteLineMutation.mutate({ lineId: line.id }) }}
                              className="text-xs font-medium text-slate-400 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded-md transition-colors"
                            >Del</button>
                          </div>
                        </td>
                      </tr>

                      {/* Expanded detail row — RM chain only */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={RM_COLS} className="border-t border-sky-200/60 bg-sky-50/30 px-5 py-4">
                            <div className="w-64">
                              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">RM Chain</p>
                              {rm ? (
                                <table className="w-full">
                                  <tbody>
                                    <RmRow label="Part Wt / pc"    value={n(rm.part_weight, 3) + " kg"} />
                                    <RmRow label="Blank Wt / pc"   value={n(rm.blank_weight, 3) + " kg"} />
                                    <RmRow label="Total Part Wt"   value={n(rm.total_part_weight, 3) + " kg"} bold />
                                    <RmRow label="Total Blank Wt"  value={n(rm.total_blank_weight, 3) + " kg"} bold />
                                    <RmRow label="Blank Rate"      value={"₹" + n(rm.blank_rate, 4) + "/kg"} />
                                    <RmRow label="Blank Cost"      value={"₹" + n(rm.blank_cost)} />
                                    <RmRow label={`Proc Loss (${n(rm.process_loss_pct, 0)}%)`} value={n(rm.process_loss_weight, 3) + " kg"} />
                                    <RmRow label="Scrap Credit"    value={"₹" + n(rm.scrap_cost)} />
                                    <RmRow label="RM Cost"         value={"₹" + n(rm.rm_cost)} bold />
                                  </tbody>
                                </table>
                              ) : (
                                <p className="text-xs text-slate-400 italic">Select grade + band to compute.</p>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── Bought-Out Items ── */}
      <section>
        <SectionHead>Bought-Out Items</SectionHead>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500">
                <th className="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[11px] w-10">#</th>
                <th className="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[11px]">Description</th>
                <th className="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[11px] w-24">Qty</th>
                <th className="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[11px] w-36">Unit Price (₹)</th>
                <th className="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[11px] w-36">Line Cost (₹)</th>
                <th className="px-4 py-3 w-8" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {boItems.length === 0 && !boFormOpen && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-xs text-slate-400 italic">
                    No bought-out items added.
                  </td>
                </tr>
              )}
              {boItems.map(item => (
                <tr key={item.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-2.5 text-slate-400 font-mono">{item.sl_no}</td>
                  <td className="px-4 py-2.5 text-slate-700">{item.description ?? "—"}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-mono">{n(item.qty, 0)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-mono">{n(item.unit_price)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-mono font-semibold">{n(item.bo_line_cost)}</td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      onClick={() => { if (confirm("Remove this item?")) deleteBoMutation.mutate({ itemId: item.id }) }}
                      className="text-slate-300 hover:text-red-500 transition-colors px-1"
                    >✕</button>
                  </td>
                </tr>
              ))}

              {/* Add form row */}
              {boFormOpen && (
                <tr className="bg-sky-50/30">
                  <td className="px-4 py-2 text-slate-400 font-mono">—</td>
                  <td className="px-4 py-2">
                    <input
                      placeholder="Description (optional)"
                      value={boForm.description}
                      onChange={e => setBoForm(p => ({ ...p, description: e.target.value }))}
                      className={cn(ic, "w-full min-w-[160px]")}
                    />
                  </td>
                  <td className="px-4 py-2">
                    <input
                      type="number" min="1" step="1"
                      value={boForm.qty}
                      onChange={e => setBoForm(p => ({ ...p, qty: e.target.value }))}
                      className={cn(ic, "w-20 text-right")}
                    />
                  </td>
                  <td className="px-4 py-2">
                    <input
                      type="number" min="0" step="0.01"
                      value={boForm.unit_price}
                      onChange={e => setBoForm(p => ({ ...p, unit_price: e.target.value }))}
                      className={cn(ic, "w-28 text-right")}
                    />
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums font-mono text-slate-400">
                    {n(String(Number(boForm.qty) * Number(boForm.unit_price)))}
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex gap-1">
                      <Button size="sm" onClick={() => addBoMutation.mutate()} disabled={addBoMutation.isPending}>
                        {addBoMutation.isPending ? "…" : "Add"}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setBoFormOpen(false)}>✕</Button>
                    </div>
                  </td>
                </tr>
              )}

              {/* Total */}
              {boItems.length > 0 && (
                <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold">
                  <td colSpan={4} className="px-4 py-2.5 text-slate-500 text-[11px] uppercase tracking-wide">
                    Total BO Cost
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-mono">
                    {n(String(boItems.reduce((s, i) => s + Number(i.bo_line_cost), 0)))}
                  </td>
                  <td />
                </tr>
              )}
            </tbody>
          </table>

          {!boFormOpen && (
            <div className="px-4 py-3 border-t border-slate-100">
              <button
                onClick={() => setBoFormOpen(true)}
                className="text-xs font-medium text-primary hover:text-primary/80 border border-primary/20 rounded px-2.5 py-1 bg-white"
              >
                + Add Item
              </button>
            </div>
          )}
        </div>
      </section>

      {/* ── Process Cost ── */}
      <section>
        <SectionHead>Process Cost</SectionHead>
        <ProcessCostSection
          sheet={sheet}
          normsLookup={normsLookup}
          gradeMap={gradeMap}
          onEditLine={openEdit}
          onDeleteLine={(lineId) => deleteLineMutation.mutate({ lineId })}
        />
      </section>

      {/* ── Sheet Finishing Operations ── */}
      <section>
        <SectionHead>Sheet Finishing Operations</SectionHead>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500">
                <th className="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[11px]">Operation</th>
                <th className="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[11px] w-32">Input Qty</th>
                <th className="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[11px] w-40">Computed Cost (₹)</th>
                <th className="px-4 py-3 w-8" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {finOps.length === 0 && !finFormOpen && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-xs text-slate-400 italic">
                    No finishing operations added.
                  </td>
                </tr>
              )}
              {finOps.map(op => (
                <tr key={op.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-2.5 font-medium text-slate-700">{op.operation_name}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-mono">{n(op.input_qty)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-mono font-semibold">{n(op.computed_cost)}</td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      onClick={() => { if (confirm("Remove this finishing op?")) deleteFinMutation.mutate({ opId: op.id }) }}
                      className="text-slate-300 hover:text-red-500 transition-colors px-1"
                    >✕</button>
                  </td>
                </tr>
              ))}

              {finFormOpen && (
                <tr className="bg-sky-50/30">
                  <td className="px-4 py-2">
                    <select
                      value={finForm.operation_name}
                      onChange={e => setFinForm(p => ({ ...p, operation_name: e.target.value }))}
                      className={cn(ic, "min-w-[200px]")}
                    >
                      <option value="">— select operation —</option>
                      {processRateNames.map(name => (
                        <option key={name} value={name}>{name}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <input
                      type="number" min="0" step="any"
                      value={finForm.input_qty}
                      onChange={e => setFinForm(p => ({ ...p, input_qty: e.target.value }))}
                      className={cn(ic, "w-28 text-right")}
                    />
                  </td>
                  <td className="px-4 py-2 text-right text-slate-400 font-mono">—</td>
                  <td className="px-4 py-2">
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        onClick={() => addFinMutation.mutate()}
                        disabled={addFinMutation.isPending || !finForm.operation_name}
                      >
                        {addFinMutation.isPending ? "…" : "Add"}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setFinFormOpen(false)}>✕</Button>
                    </div>
                  </td>
                </tr>
              )}

              {finOps.length > 0 && (
                <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold">
                  <td colSpan={2} className="px-4 py-2.5 text-slate-500 text-[11px] uppercase tracking-wide">
                    Total Finishing Cost
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-mono">
                    {n(String(finOps.reduce((s, o) => s + Number(o.computed_cost), 0)))}
                  </td>
                  <td />
                </tr>
              )}
            </tbody>
          </table>

          {!finFormOpen && (
            <div className="px-4 py-3 border-t border-slate-100">
              <button
                onClick={() => setFinFormOpen(true)}
                className="text-xs font-medium text-primary hover:text-primary/80 border border-primary/20 rounded px-2.5 py-1 bg-white"
              >
                + Add Finishing Op
              </button>
            </div>
          )}
        </div>
      </section>

      {/* ── Sheet Settings + Result ── */}
      <section>
        <SectionHead>Sheet Settings &amp; Results</SectionHead>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">

          {/* Editable settings */}
          <div className="flex flex-wrap items-end gap-5 pb-4 border-b border-slate-100">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">Discount %</p>
              {settingsEditing ? (
                <input
                  type="number" min="0" max="100" step="0.1"
                  value={settingsForm.discount_pct}
                  onChange={e => setSettingsForm(p => ({ ...p, discount_pct: e.target.value }))}
                  className={cn(ic, "w-24")}
                />
              ) : (
                <p className="text-sm font-semibold text-slate-800">{n(sheet.discount_pct, 1)} %</p>
              )}
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">Transport Cost (₹)</p>
              {settingsEditing ? (
                <input
                  type="number" min="0" step="0.01"
                  value={settingsForm.transport_cost}
                  onChange={e => setSettingsForm(p => ({ ...p, transport_cost: e.target.value }))}
                  className={cn(ic, "w-32")}
                />
              ) : (
                <p className="text-sm font-semibold text-slate-800">₹ {n(sheet.transport_cost)}</p>
              )}
            </div>
            <div className="flex gap-2 pb-0.5">
              {settingsEditing ? (
                <>
                  <Button size="sm" onClick={() => updateSheetMutation.mutate()} disabled={updateSheetMutation.isPending}>
                    {updateSheetMutation.isPending ? "Saving…" : "Save"}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setSettingsEditing(false)}>Cancel</Button>
                </>
              ) : (
                <Button size="sm" variant="outline" onClick={startEditSettings}>Edit</Button>
              )}
            </div>
          </div>

          {/* Three-block result */}
          {lines.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 py-12 text-center">
              <p className="text-xs text-slate-400">Add lines to see the cost breakdown.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-4">
                {sr ? (
                  <>
                    <BlockCard title="RM Block" block={sr.rm_block} accent="bg-amber-50/60 border-amber-200/60" />
                    <BlockCard title="BO Block" block={sr.bo_block} accent="bg-blue-50/60 border-blue-200/60" />
                  </>
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-200 flex-1 min-w-[200px] py-8 flex items-center justify-center">
                    <p className="text-xs text-slate-400">
                      Click <strong className="text-slate-600">Save Sheet</strong> for RM &amp; BO blocks.
                    </p>
                  </div>
                )}
                <BlockCard title="Process Block" block={liveProcessBlock} accent="bg-violet-50/60 border-violet-200/60" />
              </div>

              {/* Final summary — only when sr is available */}
              {sr && (
                <div className="rounded-xl border border-emerald-200/60 bg-emerald-50/40 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Final Price</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-x-8 gap-y-1 text-xs">
                    <FinalItem label="RM Grand Total"     value={"₹" + n(sr.rm_block.grand_total)} />
                    <FinalItem label="BO Grand Total"     value={"₹" + n(sr.bo_block.grand_total)} />
                    <FinalItem label="Process Grand Total" value={"₹" + n(liveProcessBlock.grand_total)} />
                    <FinalItem label="Unit Price"          value={"₹" + n(String(Number(sr.rm_block.grand_total) + Number(sr.bo_block.grand_total) + Number(liveProcessBlock.grand_total)))} bold />
                    <FinalItem
                      label={`Discount (${n(sr.discount_pct, 1)}%)`}
                      value={"−₹" + n(String((Number(sr.rm_block.grand_total) + Number(sr.bo_block.grand_total) + Number(liveProcessBlock.grand_total)) * Number(sr.discount_pct) / 100))}
                    />
                    <FinalItem label="Transport (flat)" value={"₹" + n(sr.transport_cost)} />
                  </div>
                  <div className="mt-3 pt-3 border-t border-emerald-200/60 grid grid-cols-2 sm:grid-cols-3 gap-x-8 gap-y-1 text-xs">
                    <FinalItem label="Price After Discount" value={"₹" + n(sr.price_after_discount)} bold />
                    <FinalItem label="Bal Margin"            value={"₹" + n(sr.bal_margin)} />
                    <FinalItem label="Bal Margin / kg"       value={"₹" + n(sr.bal_margin_per_kg)} bold />
                    <FinalItem label="Total Part Weight"     value={n(sr.total_part_weight, 3) + " kg"} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* ── Cost Breakdown ── */}
      {lines.length > 0 && sr && (
        <section>
          <SectionHead>Cost Breakdown</SectionHead>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-wrap gap-8 items-center">
            <CostBreakdownDonut
              rm={Number(sr.rm_block.grand_total)}
              bo={Number(sr.bo_block.grand_total)}
              process={Number(liveProcessBlock.grand_total)}
              unitPrice={Number(sr.rm_block.grand_total) + Number(sr.bo_block.grand_total) + Number(liveProcessBlock.grand_total)}
            />
            <div className="flex-1 min-w-[200px] space-y-2 text-xs">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-3">Cost Summary</p>
              {[
                { label: "RM Grand Total",      value: Number(sr.rm_block.grand_total),      color: "bg-indigo-500" },
                { label: "Bought-Out Total",    value: Number(sr.bo_block.grand_total),      color: "bg-emerald-500" },
                { label: "Process Total",       value: Number(liveProcessBlock.grand_total), color: "bg-amber-400" },
              ].map(row => (
                <div key={row.label} className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-sm shrink-0 ${row.color}`} />
                    <span className="text-slate-500">{row.label}</span>
                  </div>
                  <span className="font-mono font-semibold text-slate-800">₹{row.value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
              ))}
              <div className="border-t border-slate-100 pt-2 mt-2 flex justify-between items-center">
                <span className="font-semibold text-slate-700">Unit Price</span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  ₹{(Number(sr.rm_block.grand_total) + Number(sr.bo_block.grand_total) + Number(liveProcessBlock.grand_total)).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ── AI Insights ── */}
      {lines.length > 0 && (
        <section>
          <AiInsightsPanel sheetId={id} />
        </section>
      )}
    </div>
  )
}

function FinalItem({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className={bold ? "font-semibold" : ""}>
      <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">{label}</p>
      <p className={cn("tabular-nums font-mono", bold ? "text-slate-900" : "text-slate-700")}>{value}</p>
    </div>
  )
}
