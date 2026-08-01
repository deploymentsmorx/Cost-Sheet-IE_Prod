import { useCallback, useEffect, useRef, useState } from "react"
import { toast } from "sonner"
import { partsApi } from "../../api/parts"
import { cn } from "../../lib/utils"
import type { CostingLine, CostingSheetWithLines, ProcessCostRow } from "../../types/parts"
import type { NormsLookup } from "../../types/norms"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RowInputs {
  equi_spec: string
  thk: string
  unit_cut_length: string
  use_laser: boolean
  machining_rate: string
  bev_slant: string
  bev_length: string
  bend_num_bends: string
  drill_size: string
  drill_type: string
  drill_hours: string
  has_rolling: boolean
}

interface ComputedValues {
  cutting_cost: number
  machining_cost: number
  bevelling_cost: number
  bending_rate: number
  bending_cost: number
  drilling_rate: number
  drilling_cost: number
  rolling_rate: number
  rolling_cost: number
  row_total: number
  total_wt: number
}

// ---------------------------------------------------------------------------
// Local calc (mirrors backend exactly — keeps display live without server round-trip)
// ---------------------------------------------------------------------------

function computeRow(
  inputs: RowInputs,
  qty: number,
  totalWt: number,
  rateMap: Record<string, number>,
): ComputedValues {
  const thk = Number(inputs.thk) || 0
  const cutLen = Number(inputs.unit_cut_length) || 0
  const cutRate = inputs.use_laser
    ? (rateMap["Laser Cutting"] ?? 0)
    : (rateMap["Plasma Cutting"] ?? 0)
  const cuttingCost = cutLen && thk ? (cutLen * thk * qty * cutRate) / 1000 : 0

  const machRate = Number(inputs.machining_rate) || 0
  const machiningCost = machRate ? machRate * qty : 0

  const bevSlant = Number(inputs.bev_slant) || 0
  const bevLen = Number(inputs.bev_length) || 0
  const bevRate = rateMap["Bevelling"] ?? 0
  const bevellingCost = bevSlant && bevLen ? (bevLen / 1000) * bevSlant * bevRate * qty : 0

  const numBends = Number(inputs.bend_num_bends) || 0
  const bendKey = numBends === 1 ? "1 Bend" : numBends === 2 ? "2 Bend" : numBends === 3 ? "3 Bend" : ""
  const bendingRate = bendKey ? (rateMap[bendKey] ?? 0) : 0
  const bendingCost = numBends ? bendingRate * totalWt : 0

  const drillHrs = Number(inputs.drill_hours) || 0
  const drillKey =
    inputs.drill_type === "eh_hiten"
      ? "Drilling (EH/Hiten)"
      : inputs.drill_type === "ehc450_500"
      ? "Drilling (EHC450/EHC500)"
      : "Drilling"
  const drillingRate = rateMap[drillKey] ?? 0
  const drillingCost = drillHrs ? drillHrs * qty * drillingRate : 0

  const rollingRate = rateMap["Rolling"] ?? 0
  const rollingCost = inputs.has_rolling ? rollingRate * totalWt : 0

  return {
    cutting_cost: cuttingCost,
    machining_cost: machiningCost,
    bevelling_cost: bevellingCost,
    bending_rate: bendingRate,
    bending_cost: bendingCost,
    drilling_rate: drillingRate,
    drilling_cost: drillingCost,
    rolling_rate: rollingRate,
    rolling_cost: rollingCost,
    row_total:
      cuttingCost + machiningCost + bevellingCost + bendingCost + drillingCost + rollingCost,
    total_wt: totalWt,
  }
}

function rowToInputs(row: ProcessCostRow): RowInputs {
  return {
    equi_spec: row.equi_spec ?? "",
    thk: row.thk ?? "",
    unit_cut_length: row.unit_cut_length ?? "",
    use_laser: row.use_laser,
    machining_rate: row.machining_rate ?? "",
    bev_slant: row.bev_slant ?? "",
    bev_length: row.bev_length ?? "",
    bend_num_bends: row.bend_num_bends != null ? String(row.bend_num_bends) : "",
    drill_size: row.drill_size ?? "",
    drill_type: row.drill_type ?? "regular",
    drill_hours: row.drill_hours ?? "",
    has_rolling: row.has_rolling,
  }
}

// ---------------------------------------------------------------------------
// Number formatter
// ---------------------------------------------------------------------------

function n(v: number, dp = 2) {
  if (!v) return "—"
  return v.toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

// ---------------------------------------------------------------------------
// Shared cell classes
// ---------------------------------------------------------------------------

const TH = "px-2 py-2 text-[10px] font-bold uppercase tracking-wider whitespace-nowrap border-r border-slate-200 last:border-r-0"
const TD = "px-2 py-1.5 text-xs border-r border-slate-100 last:border-r-0"
const INPUT = "border border-slate-200 rounded px-1.5 py-1 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-sky-300 tabular-nums w-full"
const CALC = "tabular-nums font-mono text-violet-700 text-right"

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  sheet: CostingSheetWithLines
  normsLookup: NormsLookup | undefined
  onRowSaved: (updated: ProcessCostRow) => void
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ProcessCostTable({ sheet, normsLookup, onRowSaved }: Props) {
  const lines = sheet.lines
  const processRows = sheet.process_rows

  // Build maps
  const lineMap = Object.fromEntries(lines.map(l => [l.id, l])) as Record<number, CostingLine>
  const rateMap: Record<string, number> = Object.fromEntries(
    (normsLookup?.process_rates ?? []).map(pr => [pr.operation_name, Number(pr.rate)])
  )

  // Local state: inputs and computed per row (keyed by process_cost_row.id)
  const [inputs, setInputs] = useState<Record<number, RowInputs>>(() =>
    Object.fromEntries(processRows.map(r => [r.id, rowToInputs(r)]))
  )
  const [computed, setComputed] = useState<Record<number, ComputedValues>>(() => {
    const init: Record<number, ComputedValues> = {}
    for (const row of processRows) {
      const line = lineMap[row.costing_line_id]
      if (!line) continue
      const totalWt = Number(row.total_wt) || Number(line.part_weight) * Number(line.qty)
      init[row.id] = computeRow(rowToInputs(row), Number(line.qty), totalWt, rateMap)
    }
    return init
  })

  // Sync when sheet reloads (e.g. after Save Sheet)
  useEffect(() => {
    setInputs(Object.fromEntries(processRows.map(r => [r.id, rowToInputs(r)])))
    setComputed(() => {
      const next: Record<number, ComputedValues> = {}
      for (const row of processRows) {
        const line = lineMap[row.costing_line_id]
        if (!line) continue
        const totalWt = Number(row.total_wt) || Number(line.part_weight) * Number(line.qty)
        next[row.id] = computeRow(rowToInputs(row), Number(line.qty), totalWt, rateMap)
      }
      return next
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sheet.id, processRows.length])

  // Debounce timers per row
  const timers = useRef<Record<number, ReturnType<typeof setTimeout>>>({})

  const handleChange = useCallback(
    (rowId: number, field: keyof RowInputs, value: string | boolean) => {
      const row = processRows.find(r => r.id === rowId)
      if (!row) return
      const line = lineMap[row.costing_line_id]
      if (!line) return

      const next = { ...inputs[rowId], [field]: value }
      setInputs(prev => ({ ...prev, [rowId]: next }))

      const totalWt = computed[rowId]?.total_wt ?? Number(line.part_weight) * Number(line.qty)
      setComputed(prev => ({
        ...prev,
        [rowId]: computeRow(next, Number(line.qty), totalWt, rateMap),
      }))

      clearTimeout(timers.current[rowId])
      timers.current[rowId] = setTimeout(async () => {
        try {
          const payload: Record<string, unknown> = {}
          for (const k of Object.keys(next) as (keyof RowInputs)[]) {
            const v = next[k]
            if (typeof v === "boolean") {
              payload[k] = v
            } else if (v === "") {
              payload[k] = null
            } else if (k === "bend_num_bends") {
              payload[k] = Number(v)
            } else {
              payload[k] = v
            }
          }
          const updated = await partsApi.updateProcessRow(rowId, payload)
          onRowSaved(updated)
          // Update total_wt from server response
          const serverTotalWt = Number(updated.total_wt) || totalWt
          setComputed(prev => ({
            ...prev,
            [rowId]: computeRow(next, Number(line.qty), serverTotalWt, rateMap),
          }))
        } catch (e) {
          toast.error((e as Error).message)
        }
      }, 700)
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [inputs, computed, processRows, lineMap, rateMap]
  )

  if (lines.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-6 py-10 text-center text-xs text-slate-400 italic">
        Add RM lines first — process cost rows are created automatically for each line.
      </div>
    )
  }

  const tableTotal = processRows.reduce((s, r) => s + (computed[r.id]?.row_total ?? 0), 0)

  const cuttingRef = rateMap["Plasma Cutting"] ?? 0
  const laserRef = rateMap["Laser Cutting"] ?? 0
  const bevRef = rateMap["Bevelling"] ?? 0
  const drillRef = rateMap["Drilling"] ?? 0
  const drillEhRef = rateMap["Drilling (EH/Hiten)"] ?? 0
  const drillEhcRef = rateMap["Drilling (EHC450/EHC500)"] ?? 0
  const rollRef = rateMap["Rolling"] ?? 0
  const bend1Ref = rateMap["1 Bend"] ?? 0
  const bend2Ref = rateMap["2 Bend"] ?? 0
  const bend3Ref = rateMap["3 Bend"] ?? 0

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
      <table className="text-xs whitespace-nowrap border-collapse" style={{ minWidth: "2600px" }}>
        <thead>
          {/* ── Row 1: group headers ── */}
          <tr className="bg-slate-700 text-white text-center">
            <th className={cn(TH, "bg-slate-700 text-left")} rowSpan={2}>SL NO</th>
            <th className={cn(TH, "bg-slate-700 text-left")} rowSpan={2}>PART NO.</th>
            <th className={cn(TH, "bg-slate-700 text-left min-w-[140px]")} rowSpan={2}>DESCRIPTION</th>
            <th className={cn(TH, "bg-slate-700 text-left")} rowSpan={2}>SPEC.</th>
            <th className={cn(TH, "bg-slate-700 text-left")} rowSpan={2}>EQUI. SPEC.</th>
            <th className={cn(TH, "bg-slate-700 text-right")} rowSpan={2}>QTY.</th>
            <th className={cn(TH, "bg-slate-700 text-right")} rowSpan={2}>THK.</th>
            <th className={cn(TH, "bg-slate-700 text-right")} rowSpan={2}>TOTAL WT.</th>
            <th className={cn(TH, "bg-slate-700 text-right")} rowSpan={2}>UNIT CUT.<br />LENGTH</th>
            <th className={cn(TH, "bg-slate-700 text-right")} rowSpan={2}>TOTAL<br />CUTTING COST</th>
            <th className={cn(TH, "bg-sky-800")} colSpan={2}>MACHINING</th>
            <th className={cn(TH, "bg-emerald-800")} colSpan={3}>BEVELLING</th>
            <th className={cn(TH, "bg-amber-700")} colSpan={3}>BENDING</th>
            <th className={cn(TH, "bg-purple-800")} colSpan={4}>DRILLING</th>
            <th className={cn(TH, "bg-rose-800")} colSpan={2}>ROLLING</th>
            <th className={cn(TH, "bg-slate-800 text-right")} rowSpan={2}>TOTAL<br />PROCESS COST</th>
          </tr>
          {/* ── Row 2: sub-headers ── */}
          <tr className="bg-slate-600 text-white text-center text-[10px]">
            <th className={cn(TH, "bg-sky-700")}>RATE</th>
            <th className={cn(TH, "bg-sky-700")}>COST</th>
            <th className={cn(TH, "bg-emerald-700")}>SLANT</th>
            <th className={cn(TH, "bg-emerald-700")}>LENGTH</th>
            <th className={cn(TH, "bg-emerald-700")}>COST</th>
            <th className={cn(TH, "bg-amber-600")}>NO. OF BENDS</th>
            <th className={cn(TH, "bg-amber-600")}>RATE</th>
            <th className={cn(TH, "bg-amber-600")}>COST</th>
            <th className={cn(TH, "bg-purple-700")}>SIZE</th>
            <th className={cn(TH, "bg-purple-700")}>TYPE</th>
            <th className={cn(TH, "bg-purple-700")}>No. of Hrs</th>
            <th className={cn(TH, "bg-purple-700")}>RATE</th>
            <th className={cn(TH, "bg-purple-700")}>COST</th>
            <th className={cn(TH, "bg-rose-700")}>USE / RATE</th>
            <th className={cn(TH, "bg-rose-700")}>COST</th>
          </tr>

          {/* ── Reference rates row ── */}
          <tr className="bg-sky-50 border-y border-sky-200 text-slate-600 text-[10px]">
            <td className={cn(TD, "font-semibold text-sky-700 text-[10px]")} colSpan={9}>
              ▸ Current Norms Rates
            </td>
            <td className={cn(TD, "text-right font-mono")}>
              Cut: ₹{cuttingRef}/mm/m<br />
              <span className="text-indigo-600">Laser: ₹{laserRef}/mm/m</span>
            </td>
            {/* Machining */}
            <td className={cn(TD, "text-center text-slate-400 italic")}>manual</td>
            <td className={TD} />
            {/* Bevelling */}
            <td colSpan={2} className={TD} />
            <td className={cn(TD, "text-right font-mono")}>Bev: ₹{bevRef}/slant/m</td>
            {/* Bending */}
            <td className={TD} />
            <td className={cn(TD, "text-right font-mono text-[9px]")}>
              1B: ₹{bend1Ref}<br />
              2B: ₹{bend2Ref}<br />
              3B: ₹{bend3Ref}
            </td>
            <td className={TD} />
            {/* Drilling */}
            <td colSpan={2} className={TD} />
            <td className={cn(TD, "text-right font-mono text-[9px]")}>
              Reg: ₹{drillRef}<br />
              EH: ₹{drillEhRef}<br />
              EHC: ₹{drillEhcRef}
            </td>
            <td className={cn(TD, "text-right font-mono")}>Drill rate</td>
            <td className={TD} />
            {/* Rolling */}
            <td className={cn(TD, "text-right font-mono")}>₹{rollRef}/kg</td>
            <td className={TD} />
            <td className={TD} />
          </tr>
        </thead>

        <tbody className="divide-y divide-slate-100">
          {processRows.map((row) => {
            const line = lineMap[row.costing_line_id]
            if (!line) return null
            const inp = inputs[row.id] ?? rowToInputs(row)
            const calc = computed[row.id]
            const partNo = sheet.part_no ?? "—"

            const ic = cn(INPUT)

            function field(
              key: keyof RowInputs,
              type: "text" | "number" = "number",
              placeholder = "",
              width = "w-16"
            ) {
              return (
                <input
                  type={type}
                  min={type === "number" ? "0" : undefined}
                  step={type === "number" ? "any" : undefined}
                  placeholder={placeholder}
                  value={inp[key] as string}
                  onChange={e => handleChange(row.id, key, e.target.value)}
                  className={cn(ic, width)}
                />
              )
            }

            function calcCell(val: number | undefined) {
              return (
                <td className={cn(TD, CALC)}>
                  {val ? "₹" + n(val) : <span className="text-slate-300">—</span>}
                </td>
              )
            }

            return (
              <tr key={row.id} className="hover:bg-slate-50/50 align-middle">
                {/* Pre-filled (read-only) */}
                <td className={cn(TD, "text-slate-400 font-mono")}>{line.sl_no}</td>
                <td className={cn(TD, "text-slate-500 font-mono")}>{partNo}</td>
                <td className={cn(TD, "max-w-[160px] truncate font-medium text-slate-800")}>
                  {line.description ?? "—"}
                </td>
                <td className={cn(TD, "text-slate-500")}>{line.spec ?? "—"}</td>

                {/* Equi. Spec. — editable */}
                <td className={TD}>
                  <input
                    type="text"
                    placeholder="equi. spec"
                    value={inp.equi_spec}
                    onChange={e => handleChange(row.id, "equi_spec", e.target.value)}
                    className={cn(ic, "w-24")}
                  />
                </td>

                {/* QTY — read-only */}
                <td className={cn(TD, "text-right tabular-nums text-slate-700")}>
                  {Number(line.qty).toLocaleString("en-IN")}
                </td>

                {/* THK — manual */}
                <td className={TD}>{field("thk", "number", "mm", "w-14")}</td>

                {/* TOTAL WT — from RM result */}
                <td className={cn(TD, "text-right tabular-nums font-mono text-slate-600")}>
                  {n(calc?.total_wt ?? 0, 3)} kg
                </td>

                {/* UNIT CUT LENGTH + laser toggle */}
                <td className={TD}>
                  <div className="flex flex-col gap-1">
                    {field("unit_cut_length", "number", "mm", "w-16")}
                    <label className="flex items-center gap-1 text-[10px] text-indigo-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={inp.use_laser}
                        onChange={e => handleChange(row.id, "use_laser", e.target.checked)}
                        className="accent-indigo-500"
                      />
                      Laser
                    </label>
                  </div>
                </td>

                {/* TOTAL CUTTING COST */}
                {calcCell(calc?.cutting_cost)}

                {/* MACHINING */}
                <td className={TD}>{field("machining_rate", "number", "rate", "w-16")}</td>
                {calcCell(calc?.machining_cost)}

                {/* BEVELLING */}
                <td className={TD}>{field("bev_slant", "number", "slants", "w-14")}</td>
                <td className={TD}>{field("bev_length", "number", "mm", "w-16")}</td>
                {calcCell(calc?.bevelling_cost)}

                {/* BENDING */}
                <td className={TD}>
                  <select
                    value={inp.bend_num_bends}
                    onChange={e => handleChange(row.id, "bend_num_bends", e.target.value)}
                    className={cn(ic, "w-16")}
                  >
                    <option value="">—</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                  </select>
                </td>
                <td className={cn(TD, CALC)}>
                  {calc?.bending_rate ? n(calc.bending_rate) : <span className="text-slate-300">—</span>}
                </td>
                {calcCell(calc?.bending_cost)}

                {/* DRILLING */}
                <td className={TD}>{field("drill_size", "text", "size", "w-16")}</td>
                <td className={TD}>
                  <select
                    value={inp.drill_type}
                    onChange={e => handleChange(row.id, "drill_type", e.target.value)}
                    className={cn(ic, "w-24")}
                  >
                    <option value="regular">Regular</option>
                    <option value="eh_hiten">EH/Hiten</option>
                    <option value="ehc450_500">EHC450-500</option>
                  </select>
                </td>
                <td className={TD}>{field("drill_hours", "number", "hrs", "w-14")}</td>
                <td className={cn(TD, CALC)}>
                  {calc?.drilling_rate ? n(calc.drilling_rate) : <span className="text-slate-300">—</span>}
                </td>
                {calcCell(calc?.drilling_cost)}

                {/* ROLLING */}
                <td className={TD}>
                  <div className="flex flex-col items-start gap-1">
                    <label className="flex items-center gap-1 text-[10px] text-rose-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={inp.has_rolling}
                        onChange={e => handleChange(row.id, "has_rolling", e.target.checked)}
                        className="accent-rose-500"
                      />
                      Use
                    </label>
                    <span className={cn("font-mono tabular-nums", inp.has_rolling ? "text-rose-700" : "text-slate-300")}>
                      {inp.has_rolling ? `₹${n(calc?.rolling_rate ?? 0)}/kg` : "—"}
                    </span>
                  </div>
                </td>
                {calcCell(calc?.rolling_cost)}

                {/* TOTAL PROCESS COST */}
                <td className={cn(TD, "text-right font-semibold font-mono tabular-nums text-slate-900 bg-slate-50/60")}>
                  {calc?.row_total ? "₹" + n(calc.row_total) : <span className="text-slate-300">—</span>}
                </td>
              </tr>
            )
          })}
        </tbody>

        {/* ── Table footer — grand total ── */}
        <tfoot>
          <tr className="bg-slate-100 border-t-2 border-slate-300 font-semibold">
            <td colSpan={25} className={cn(TD, "text-right text-slate-600 text-[11px] uppercase tracking-wide pr-3")}>
              Total Process Cost
            </td>
            <td className={cn(TD, "text-right font-mono tabular-nums text-slate-900 text-sm")}>
              {tableTotal ? "₹" + n(tableTotal) : "—"}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
