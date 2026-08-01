import { Fragment, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { partsApi } from "../../api/parts"
import { Button } from "../ui/button"
import { cn } from "../../lib/utils"
import type { CostingLine, CostingSheetWithLines } from "../../types/parts"
import type { NormsLookup, ProcessRate } from "../../types/norms"

// ---------------------------------------------------------------------------
// Group mapping
// ---------------------------------------------------------------------------

const OP_GROUP: Record<string, string> = {
  "CUTTING COST":               "Material Cutting",
  "LASER CUTTING":              "Material Cutting",
  "BEVELLING COST":             "Material Cutting",
  "1 BEND":                     "Forming",
  "2 BEND":                     "Forming",
  "3 BEND":                     "Forming",
  "ROLLING":                    "Forming",
  "DRILLING":                   "Drilling",
  "DRILLING EH/HITEN":          "Drilling",
  "DRILLING EHC450/EHC500":     "Drilling",
  "TACK WELDING":               "Welding",
  "FULL WELDING solid wire":    "Welding",
  "DRESSING":                   "Welding",
  "SANDERING":                  "Welding",
  "GAUGING":                    "Welding",
  "PREHEATING/HEAT CORRECTION": "Welding",
  "STRAIGHTENING":              "Welding",
  "SHOT BLASTING":              "Surface Treatment",
  "ZINC PLATING":               "Surface Treatment",
  "GALVANIZING":                "Surface Treatment",
  "FINAL PAINTING":             "Surface Treatment",
  "MACHINING VTL":              "Machining",
  "SUB TRANSPORT":              "Machining",
  "BUSH FITTING":               "Bush Fitting",
}

const GROUPS = [
  "Material Cutting", "Forming", "Drilling", "Welding",
  "Surface Treatment", "Machining", "Bush Fitting", "Others",
]

// 9 columns: Sl | Description | Spec | Group | Operation | Inputs | Rate | Cost (₹) | Actions
const COL_COUNT = 9

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function n(v: string | number | undefined | null, dp = 2) {
  if (v == null || v === "") return "—"
  return Number(v).toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

function getFields(unit: string): { key: string; label: string }[] {
  if (unit === "Rs/mm/meter")    return [{ key: "length_mm",      label: "Cut Length (mm)" }]
  if (unit === "Rs/slant/meter") return [
    { key: "slant_length_mm", label: "Slant Length (mm)" },
    { key: "num_slants",      label: "No. of Slants" },
  ]
  if (unit === "Rs/Hr")  return [{ key: "hours",     label: "Hours" }]
  if (unit === "Rs/Nos") return [{ key: "input_qty", label: "Qty (Nos)" }]
  if (unit === "Rs/Sqm") return [{ key: "input_qty", label: "Area (Sqm)" }]
  return []
}

function previewCost(
  unit: string,
  inputs: Record<string, string>,
  rate: number,
  thicknessMm: number,
  qty: number,
  totalWt: number,
): number {
  if (unit === "Rs/mm/meter")    return (Number(inputs.length_mm || 0) / 1000) * thicknessMm * qty * rate
  if (unit === "Rs/slant/meter") return (Number(inputs.slant_length_mm || 0) / 1000) * Number(inputs.num_slants || 1) * rate * qty
  if (unit === "Rs/Kg")          return totalWt * rate
  if (unit === "Rs/Hr")          return Number(inputs.hours || 0) * qty * rate
  if (unit === "Rs/Nos" || unit === "Rs/Sqm") return Number(inputs.input_qty || 0) * rate
  return 0
}

function formulaLines(
  unit: string,
  inputData: Record<string, unknown>,
  rate: number,
  thicknessMm: number,
  qty: number,
  totalWt: number,
  cost: number,
): string[] {
  const r = (v: number) => v.toLocaleString("en-IN", { maximumFractionDigits: 4 })
  if (unit === "Rs/mm/meter") {
    const len = Number(inputData.length_mm ?? 0)
    return [
      `Formula: (cut_length ÷ 1000) × thickness × qty × rate`,
      `= (${r(len)} ÷ 1000) × ${r(thicknessMm)} mm × ${r(qty)} × ₹${r(rate)}/mm/m`,
      `= ₹${r(cost)}`,
    ]
  }
  if (unit === "Rs/slant/meter") {
    const sl = Number(inputData.slant_length_mm ?? 0)
    const ns = Number(inputData.num_slants ?? 1)
    return [
      `Formula: (slant_length ÷ 1000) × slants × rate × qty`,
      `= (${r(sl)} ÷ 1000) × ${r(ns)} × ₹${r(rate)}/slant/m × ${r(qty)}`,
      `= ₹${r(cost)}`,
    ]
  }
  if (unit === "Rs/Kg") {
    return [
      `Formula: total_part_weight × rate`,
      `= ${r(totalWt)} kg × ₹${r(rate)}/kg`,
      `= ₹${r(cost)}`,
    ]
  }
  if (unit === "Rs/Hr") {
    const hrs = Number(inputData.hours ?? 0)
    return [
      `Formula: hours × qty × rate`,
      `= ${r(hrs)} hr × ${r(qty)} pcs × ₹${r(rate)}/hr`,
      `= ₹${r(cost)}`,
    ]
  }
  if (unit === "Rs/Nos") {
    const iq = Number(inputData.input_qty ?? 0)
    return [`Formula: qty_nos × rate`, `= ${r(iq)} nos × ₹${r(rate)}/nos`, `= ₹${r(cost)}`]
  }
  if (unit === "Rs/Sqm") {
    const iq = Number(inputData.input_qty ?? 0)
    return [`Formula: area × rate`, `= ${r(iq)} sqm × ₹${r(rate)}/sqm`, `= ₹${r(cost)}`]
  }
  return [`Cost: ₹${r(cost)}`]
}

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

function FormulaTooltip({ lines, children }: { lines: string[]; children: React.ReactNode }) {
  return (
    <span className="relative group/tooltip inline-block">
      {children}
      <span className="pointer-events-none absolute bottom-full right-0 mb-2 hidden group-hover/tooltip:flex flex-col gap-0.5 z-50 min-w-[280px]">
        <span className="bg-slate-900 text-slate-100 rounded-lg px-3 py-2.5 shadow-xl text-[11px] font-mono whitespace-nowrap">
          {lines.map((l, i) => (
            <span key={i} className={cn("block", i === lines.length - 1 && "text-violet-300 font-semibold mt-1")}>
              {l}
            </span>
          ))}
        </span>
        <span className="self-end mr-3 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-slate-900" />
      </span>
    </span>
  )
}

// ---------------------------------------------------------------------------
// Add / Edit operation form (renders inside a full-width colSpan row)
// ---------------------------------------------------------------------------

interface OpFormState { group: string; opName: string; inputs: Record<string, string> }

function OpForm({
  line, normsLookup, initial, onSubmit, onCancel, submitting,
}: {
  line: CostingLine
  normsLookup: NormsLookup
  initial?: OpFormState
  onSubmit: (opName: string, inputData: Record<string, unknown>) => Promise<void>
  onCancel: () => void
  submitting: boolean
}) {
  const [form, setForm] = useState<OpFormState>(initial ?? { group: "", opName: "", inputs: {} })
  const ic = "border border-slate-200 rounded-md px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-primary/30"

  const ratesInGroup: ProcessRate[] = normsLookup.process_rates.filter(pr => {
    if (pr.unit === "%") return false
    return (OP_GROUP[pr.operation_name] ?? "Others") === form.group
  })

  const selectedRate = normsLookup.process_rates.find(pr => pr.operation_name === form.opName)
  const unit = selectedRate?.unit ?? ""
  const rate = Number(selectedRate?.rate ?? 0)
  const fields = getFields(unit)

  const totalWt = line.rm_result
    ? Number(line.rm_result.total_part_weight)
    : Number(line.part_weight) * Number(line.qty)
  const thicknessMm = Number(line.thickness_mm ?? 0)
  const qty = Number(line.qty)
  const preview = selectedRate ? previewCost(unit, form.inputs, rate, thicknessMm, qty, totalWt) : 0
  const needsThickness = unit === "Rs/mm/meter" || unit === "Rs/slant/meter"
  const missingThickness = needsThickness && thicknessMm === 0

  async function handleSubmit() {
    if (!form.opName) { toast.error("Select an operation"); return }
    if (missingThickness) {
      toast.error("This operation needs Thickness (mm) on the line — edit the line and set it first")
      return
    }
    if (unit === "Rs/Kg" && totalWt === 0) {
      toast.error("Part weight is 0 — edit the line and set Part Weight first")
      return
    }
    const inputData: Record<string, unknown> = {}
    for (const f of fields) {
      const raw = form.inputs[f.key]
      const num = Number(raw)
      if (!raw || isNaN(num) || num <= 0) {
        toast.error(`${f.label} must be a positive number`)
        return
      }
      inputData[f.key] = num
    }
    await onSubmit(form.opName, inputData)
  }

  return (
    <div className="flex flex-wrap items-end gap-2 p-3 bg-sky-50/40 rounded-lg border border-sky-200/60">
      <div>
        <label className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1 block">Group</label>
        <select value={form.group} onChange={e => setForm({ group: e.target.value, opName: "", inputs: {} })} className={cn(ic, "min-w-[160px]")}>
          <option value="">— group —</option>
          {GROUPS.map(g => <option key={g} value={g}>{g}</option>)}
        </select>
      </div>

      {form.group && (
        <div>
          <label className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1 block">Operation</label>
          <select value={form.opName} onChange={e => setForm(p => ({ ...p, opName: e.target.value, inputs: {} }))} className={cn(ic, "min-w-[220px]")}>
            <option value="">— select —</option>
            {ratesInGroup.map(pr => (
              <option key={pr.operation_name} value={pr.operation_name}>
                {pr.operation_name} ({pr.unit} @ ₹{Number(pr.rate).toFixed(2)})
              </option>
            ))}
          </select>
        </div>
      )}

      {fields.map(f => (
        <div key={f.key}>
          <label className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1 block">{f.label}</label>
          <input
            type="number" min="0.001" step="any"
            value={form.inputs[f.key] ?? ""}
            onChange={e => setForm(p => ({ ...p, inputs: { ...p.inputs, [f.key]: e.target.value } }))}
            className={cn(ic, "w-28")}
          />
        </div>
      ))}

      {unit === "Rs/Kg" && form.opName && (
        <div>
          <label className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1 block">Weight</label>
          <span className={cn(ic, "block text-slate-400 italic")}>auto · {n(totalWt, 3)} kg</span>
        </div>
      )}

      {missingThickness && (
        <div className="w-full mt-1">
          <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded px-2.5 py-1.5 font-medium">
            ⚠ This operation needs <strong>Thickness (mm)</strong> set on the line. Click <em>Edit Line</em> and enter the actual thickness in mm.
          </p>
        </div>
      )}

      {selectedRate && !missingThickness && (
        <div>
          <label className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1 block">Est. Cost</label>
          <span className="block px-2.5 py-1.5 text-xs font-mono text-violet-700 font-semibold bg-violet-50 rounded-md border border-violet-200/60">
            ₹{n(preview)}
          </span>
        </div>
      )}

      <div className="flex gap-1.5 pb-0.5">
        <Button size="sm" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Saving…" : initial ? "Update" : "Add"}
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Per-line rows — renders a line header row + one row per operation
// Columns (9, no colSpan in data rows):
//   Sl | Description | Spec | Group | Operation | Inputs | Rate | Cost (₹) | Actions
// ---------------------------------------------------------------------------

function LineRows({
  line, normsLookup, gradeMap, onSaved, onEditLine, onDeleteLine,
}: {
  line: CostingLine
  normsLookup: NormsLookup
  gradeMap: Record<number, string>
  onSaved: () => void
  onEditLine: (line: CostingLine) => void
  onDeleteLine: (lineId: number) => void
}) {
  const [addOpen, setAddOpen] = useState(false)
  const [editingOpId, setEditingOpId] = useState<number | null>(null)

  const addMutation = useMutation({
    mutationFn: ({ opName, inputData }: { opName: string; inputData: Record<string, unknown> }) =>
      partsApi.addOperation(line.id, { operation_type: opName, input_data: inputData }),
    onSuccess: () => { onSaved(); setAddOpen(false); toast.success("Operation added") },
    onError: (e: Error) => toast.error(e.message),
  })

  const updateMutation = useMutation({
    mutationFn: ({ opId, opName, inputData }: { opId: number; opName: string; inputData: Record<string, unknown> }) =>
      partsApi.updateOperation(line.id, opId, { operation_type: opName, input_data: inputData }),
    onSuccess: () => { onSaved(); setEditingOpId(null); toast.success("Operation updated") },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (opId: number) => partsApi.deleteOperation(line.id, opId),
    onSuccess: () => { onSaved(); toast.success("Operation removed") },
    onError: (e: Error) => toast.error(e.message),
  })

  const rateMap: Record<string, ProcessRate> = Object.fromEntries(
    normsLookup.process_rates.map(pr => [pr.operation_name, pr])
  )

  const totalWt = line.rm_result
    ? Number(line.rm_result.total_part_weight)
    : Number(line.part_weight) * Number(line.qty)
  const thicknessMm = Number(line.thickness_mm ?? 0)
  const qty = Number(line.qty)

  const liveCosts: number[] = line.operations.map(op => {
    const pr = rateMap[op.operation_type]
    if (!pr) return Number(op.operation_cost)
    const inputs: Record<string, string> = Object.fromEntries(
      Object.entries(op.input_data).map(([k, v]) => [k, String(v)])
    )
    return previewCost(pr.unit, inputs, Number(pr.rate), thicknessMm, qty, totalWt)
  })
  const liveTotalCost = liveCosts.reduce((s, c) => s + c, 0)

  function makeInitialEdit(op: typeof line.operations[0]): OpFormState {
    const inputs: Record<string, string> = {}
    for (const [k, v] of Object.entries(op.input_data)) inputs[k] = String(v)
    return { group: OP_GROUP[op.operation_type] ?? "Others", opName: op.operation_type, inputs }
  }

  // Sub-text shown in the Grade column of the line header row
  const gradeBand = [
    line.grade_id ? (gradeMap[line.grade_id] ?? `#${line.grade_id}`) : null,
    line.thickness_band ?? null,
  ].filter(Boolean).join(" / ")

  return (
    <Fragment>
      {/* ── Line header row ── */}
      <tr className="bg-slate-50 border-y border-slate-200 align-middle">
        {/* Sl */}
        <td className="px-3 py-2.5 font-mono text-slate-500 font-bold text-[11px]">
          {line.sl_no}
        </td>
        {/* Description */}
        <td className="px-3 py-2.5 font-semibold text-slate-900 text-xs max-w-[160px] truncate">
          {line.description ?? "—"}
        </td>
        {/* Spec */}
        <td className="px-3 py-2.5 text-slate-400 text-xs max-w-[100px] truncate">
          {line.spec ?? "—"}
        </td>
        {/* Group — shows grade/band as context */}
        <td className="px-3 py-2.5 text-slate-500 text-xs">
          {gradeBand || "—"}
        </td>
        {/* Operation — shows thickness */}
        <td className="px-3 py-2.5 text-slate-500 text-xs font-mono">
          {line.thickness_mm ? `${line.thickness_mm} mm` : "—"}
        </td>
        {/* Inputs — shows qty */}
        <td className="px-3 py-2.5 text-right tabular-nums text-xs font-mono">
          {n(line.qty, 0)}
        </td>
        {/* Rate — shows total weight */}
        <td className="px-3 py-2.5 text-right tabular-nums text-xs font-mono">
          {n(totalWt, 3)} kg
        </td>
        {/* Cost — line process total */}
        <td className="px-3 py-2.5 text-right tabular-nums font-mono font-bold text-violet-700 text-xs">
          {liveTotalCost > 0 ? n(liveTotalCost) : "—"}
        </td>
        {/* Actions */}
        <td className="px-3 py-2.5">
          <div className="flex items-center gap-0.5 justify-end">
            <button
              onClick={() => onEditLine(line)}
              className="text-[11px] font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-200 px-2 py-0.5 rounded transition-colors whitespace-nowrap"
            >
              Edit
            </button>
            <button
              onClick={() => { if (confirm("Delete this line and all its operations?")) onDeleteLine(line.id) }}
              className="text-[11px] font-medium text-slate-400 hover:text-red-600 hover:bg-red-50 px-2 py-0.5 rounded transition-colors"
            >
              Del
            </button>
            <button
              onClick={() => { setAddOpen(v => !v); setEditingOpId(null) }}
              className="text-[11px] font-medium text-primary hover:text-primary/80 border border-primary/30 rounded px-2 py-0.5 bg-white whitespace-nowrap ml-1 transition-colors"
            >
              {addOpen ? "✕" : "+ Op"}
            </button>
          </div>
        </td>
      </tr>

      {/* ── Operation rows ── */}
      {line.operations.map((op, opIdx) => {
        const pr = rateMap[op.operation_type]
        const unit = pr?.unit ?? ""
        const rate = Number(pr?.rate ?? 0)
        const group = OP_GROUP[op.operation_type] ?? "Others"
        const cost = liveCosts[opIdx]
        const isEditing = editingOpId === op.id
        const fLines = pr
          ? formulaLines(unit, op.input_data, rate, thicknessMm, qty, totalWt, cost)
          : [`Cost: ₹${cost}`]
        const inputSummary = unit === "Rs/Kg"
          ? `${n(totalWt, 3)} kg (auto)`
          : Object.entries(op.input_data).map(([k, v]) => `${k}: ${v}`).join(" · ") || "—"

        return (
          <Fragment key={op.id}>
            <tr className={cn(
              "border-b border-slate-100 hover:bg-violet-50/20 transition-colors align-middle",
              isEditing && "bg-sky-50/30 border-sky-200"
            )}>
              {/* Sl — empty */}
              <td className="px-3 py-2" />
              {/* Description — empty */}
              <td className="px-3 py-2" />
              {/* Spec — empty */}
              <td className="px-3 py-2" />
              {/* Group */}
              <td className="px-3 py-2">
                <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 rounded-full px-2 py-0.5 whitespace-nowrap">
                  {group}
                </span>
              </td>
              {/* Operation */}
              <td className="px-3 py-2 font-medium text-slate-800 text-xs whitespace-nowrap">
                {op.operation_type}
              </td>
              {/* Inputs */}
              <td className="px-3 py-2 text-slate-500 text-xs font-mono">
                {inputSummary}
              </td>
              {/* Rate */}
              <td className="px-3 py-2 text-right font-mono text-slate-500 text-xs whitespace-nowrap">
                {pr ? `₹${n(pr.rate, 2)} ${unit}` : "—"}
              </td>
              {/* Cost */}
              <td className="px-3 py-2 text-right">
                <FormulaTooltip lines={fLines}>
                  <span className="tabular-nums font-mono font-semibold text-violet-700 text-xs cursor-help underline decoration-dashed underline-offset-2 decoration-violet-300">
                    {n(cost)}
                  </span>
                </FormulaTooltip>
              </td>
              {/* Actions */}
              <td className="px-3 py-2">
                <div className="flex items-center gap-0.5 justify-end">
                  <button
                    onClick={() => { setEditingOpId(isEditing ? null : op.id); setAddOpen(false) }}
                    className="text-[11px] font-medium text-slate-400 hover:text-slate-800 hover:bg-slate-100 px-1.5 py-0.5 rounded transition-colors"
                  >
                    {isEditing ? "Close" : "Edit"}
                  </button>
                  <button
                    onClick={() => { if (confirm("Remove this operation?")) deleteMutation.mutate(op.id) }}
                    className="text-[11px] font-medium text-slate-300 hover:text-red-600 hover:bg-red-50 px-1.5 py-0.5 rounded transition-colors"
                  >
                    Del
                  </button>
                </div>
              </td>
            </tr>

            {/* Inline edit form — full width */}
            {isEditing && (
              <tr>
                <td colSpan={COL_COUNT} className="px-4 py-3 bg-sky-50/20 border-b border-sky-100">
                  <OpForm
                    line={line}
                    normsLookup={normsLookup}
                    initial={makeInitialEdit(op)}
                    onSubmit={async (opName, inputData) => {
                      await updateMutation.mutateAsync({ opId: op.id, opName, inputData })
                    }}
                    onCancel={() => setEditingOpId(null)}
                    submitting={updateMutation.isPending}
                  />
                </td>
              </tr>
            )}
          </Fragment>
        )
      })}

      {/* Empty state */}
      {line.operations.length === 0 && !addOpen && (
        <tr>
          <td colSpan={COL_COUNT} className="px-4 py-2.5 text-xs text-slate-400 italic border-b border-slate-100">
            No operations — click <span className="font-medium text-slate-500">+ Op</span> to begin.
          </td>
        </tr>
      )}

      {/* Add form — full width */}
      {addOpen && (
        <tr>
          <td colSpan={COL_COUNT} className="px-4 py-3 bg-sky-50/20 border-b border-sky-100">
            <OpForm
              line={line}
              normsLookup={normsLookup}
              onSubmit={async (opName, inputData) => {
                await addMutation.mutateAsync({ opName, inputData })
              }}
              onCancel={() => setAddOpen(false)}
              submitting={addMutation.isPending}
            />
          </td>
        </tr>
      )}
    </Fragment>
  )
}

// ---------------------------------------------------------------------------
// Exported section
// ---------------------------------------------------------------------------

export function ProcessCostSection({
  sheet,
  normsLookup,
  gradeMap,
  onEditLine,
  onDeleteLine,
}: {
  sheet: CostingSheetWithLines
  normsLookup: NormsLookup | undefined
  gradeMap: Record<number, string>
  onEditLine: (line: CostingLine) => void
  onDeleteLine: (lineId: number) => void
}) {
  const qc = useQueryClient()
  function onSaved() {
    qc.invalidateQueries({ queryKey: ["sheet", sheet.id] })
    qc.invalidateQueries({ queryKey: ["summary"] })
  }

  if (!normsLookup) {
    return <div className="text-xs text-slate-400 italic py-4">Loading norms rates…</div>
  }

  if (sheet.lines.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-6 py-8 text-center text-xs text-slate-400 italic">
        Add RM lines first to enter process cost operations.
      </div>
    )
  }

  const totalProcessCost = sheet.lines.reduce((s, ln) => s + Number(ln.line_process_cost ?? 0), 0)

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
      <table className="w-full text-xs whitespace-nowrap">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500">
            <th className="px-3 py-3 text-left font-semibold uppercase tracking-wider text-[11px] w-10">Sl</th>
            <th className="px-3 py-3 text-left font-semibold uppercase tracking-wider text-[11px]">Description</th>
            <th className="px-3 py-3 text-left font-semibold uppercase tracking-wider text-[11px]">Spec</th>
            <th className="px-3 py-3 text-left font-semibold uppercase tracking-wider text-[11px]">Group / Grade</th>
            <th className="px-3 py-3 text-left font-semibold uppercase tracking-wider text-[11px]">Operation / Thk</th>
            <th className="px-3 py-3 text-right font-semibold uppercase tracking-wider text-[11px]">Qty / Inputs</th>
            <th className="px-3 py-3 text-right font-semibold uppercase tracking-wider text-[11px]">Total Wt / Rate</th>
            <th className="px-3 py-3 text-right font-semibold uppercase tracking-wider text-[11px]">Cost (₹)</th>
            <th className="px-3 py-3 w-8" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {sheet.lines.map(line => (
            <LineRows
              key={line.id}
              line={line}
              normsLookup={normsLookup}
              gradeMap={gradeMap}
              onSaved={onSaved}
              onEditLine={onEditLine}
              onDeleteLine={onDeleteLine}
            />
          ))}

          {totalProcessCost > 0 && (
            <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold">
              <td colSpan={7} className="px-3 py-2.5 text-slate-500 text-[11px] uppercase tracking-wide">
                Total Process Cost
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums font-mono text-violet-700">
                {n(totalProcessCost)}
              </td>
              <td />
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
