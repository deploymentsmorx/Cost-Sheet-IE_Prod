import { useState } from "react"
import { Button } from "../ui/button"
import { cn } from "../../lib/utils"

interface FormulaRow {
  label: string
  formula: string
  source?: string
  sourceType?: "norms" | "manual" | "derived"
  indent?: boolean
}

const FORMULA_SECTIONS: Array<{ heading: string; rows: FormulaRow[] }> = [
  {
    heading: "Weight Chain",
    rows: [
      {
        label: "Part Weight",
        formula: "DXF Surface Area × Thickness (mm³) × 7850 ÷ 1,000,000",
        source: "Manual entry — derived from drawing",
        sourceType: "manual",
      },
      {
        label: "Total Part Weight",
        formula: "Part Weight × Quantity",
        sourceType: "derived",
      },
      {
        label: "Blank Weight (per piece)",
        formula: "Part Weight ÷ (Efficiency % ÷ 100)",
        source: "Manual entry — Efficiency % entered per line",
        sourceType: "manual",
      },
      {
        label: "Total Blank Weight",
        formula: "Blank Weight × Quantity",
        sourceType: "derived",
      },
    ],
  },
  {
    heading: "Raw Material Cost",
    rows: [
      {
        label: "Blank Rate",
        formula: "Looked up by Grade + Thickness Band",
        source: "Norms Library → RM Price Matrix",
        sourceType: "norms",
      },
      {
        label: "Blank Cost",
        formula: "Total Blank Weight × Blank Rate",
        sourceType: "derived",
      },
      {
        label: "Process Loss %",
        formula: "From PROCESS LOSS row in process rates",
        source: "Norms Library → Process Rates (Material / Cutting group)",
        sourceType: "norms",
      },
      {
        label: "Process Loss Weight",
        formula: "Total Blank Weight × (Process Loss % ÷ 100)",
        sourceType: "derived",
      },
      {
        label: "Scrap Rate",
        formula: "Rate per kg for recoverable scrap",
        source: "Norms Library → Scrap Rate",
        sourceType: "norms",
      },
      {
        label: "Scrap Weight",
        formula: "Total Blank Weight − Total Part Weight − Process Loss Weight",
        sourceType: "derived",
      },
      {
        label: "Scrap Cost",
        formula: "Scrap Weight × Scrap Rate",
        sourceType: "derived",
      },
      {
        label: "RM Cost",
        formula: "Blank Cost − Scrap Cost",
        sourceType: "derived",
      },
    ],
  },
  {
    heading: "Process Cost",
    rows: [
      {
        label: "Process Rate (per operation)",
        formula: "Looked up by operation name",
        source: "Norms Library → Process Rates",
        sourceType: "norms",
      },
      {
        label: "Process Cost",
        formula: "Σ ( Qty / Hours per piece × Quantity × Process Rate )",
        source: "Hrs/pc entered per line; rates from Norms Library → Process Rates",
        sourceType: "norms",
      },
    ],
  },
  {
    heading: "Bought-Out Cost",
    rows: [
      {
        label: "BO Cost",
        formula: "Bought-Out Price per piece × Quantity",
        source: "Manual entry",
        sourceType: "manual",
      },
    ],
  },
  {
    heading: "Overhead, Rework, Inventory & Profit",
    rows: [
      {
        label: "On RM Cost",
        formula: "RM Cost × (Overhead % + Rework % + Inventory Carry % + Profit %)",
        source: "Norms Library → Overhead Params → Raw Material",
        sourceType: "norms",
      },
      {
        label: "On BO Cost",
        formula: "BO Cost × (Overhead % + Inventory Carry % + Profit %)",
        source: "Norms Library → Overhead Params → Bought-Out Parts  [no Rework]",
        sourceType: "norms",
      },
      {
        label: "On Process Cost",
        formula: "Process Cost × (Overhead % + Rework % + Profit %)",
        source: "Norms Library → Overhead Params → Process Cost  [no Inventory]",
        sourceType: "norms",
      },
    ],
  },
  {
    heading: "Final Roll-Up",
    rows: [
      {
        label: "Transport Cost",
        formula: "Transport per piece × Quantity",
        source: "Manual entry",
        sourceType: "manual",
      },
      {
        label: "Unit Price (line total)",
        formula: "RM Cost + BO Cost + Process Cost + all overheads + Transport Cost",
        sourceType: "derived",
      },
      {
        label: "Price After Discount",
        formula: "Unit Price × ( 1 − Discount % ÷ 100 )",
        source: "Discount % — manual entry",
        sourceType: "manual",
      },
      {
        label: "Bal. Margin",
        formula: "Price After Discount − ( RM Cost + BO Cost )",
        sourceType: "derived",
      },
      {
        label: "Bal. Margin / kg",
        formula: "Bal. Margin ÷ Total Part Weight",
        sourceType: "derived",
      },
    ],
  },
]

const SOURCE_BADGE: Record<string, { label: string; cls: string }> = {
  norms:   { label: "Norms Library", cls: "bg-sky-50 text-sky-700 border-sky-200" },
  manual:  { label: "Manual entry",  cls: "bg-amber-50 text-amber-700 border-amber-200" },
  derived: { label: "Calculated",    cls: "bg-emerald-50 text-emerald-700 border-emerald-200" },
}

export function FormulasModal() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        Formulas Used
      </Button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={e => { if (e.target === e.currentTarget) setOpen(false) }}
        >
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[88vh] flex flex-col mx-4 border border-slate-200">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
              <div>
                <h2 className="text-base font-semibold text-slate-900">Calculation Formulas</h2>
                <p className="text-xs text-slate-400 mt-0.5">Reference guide for all pricing calculations</p>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-slate-400 hover:text-slate-700 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors text-lg leading-none"
              >✕</button>
            </div>

            {/* Legend */}
            <div className="flex gap-2 px-6 py-3 border-b border-slate-100 bg-slate-50/60">
              {Object.entries(SOURCE_BADGE).map(([, v]) => (
                <span key={v.label} className={cn(
                  "text-[11px] border rounded-full px-2.5 py-0.5 font-semibold",
                  v.cls
                )}>
                  {v.label}
                </span>
              ))}
            </div>

            {/* Body */}
            <div className="overflow-y-auto px-6 py-5 space-y-5">
              {FORMULA_SECTIONS.map(section => (
                <div key={section.heading}>
                  <h3 className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-2.5">
                    {section.heading}
                  </h3>
                  <div className="rounded-xl border border-slate-200 overflow-hidden">
                    <table className="w-full text-sm">
                      <tbody>
                        {section.rows.map((row, i) => {
                          const badge = row.sourceType ? SOURCE_BADGE[row.sourceType] : null
                          return (
                            <tr
                              key={row.label}
                              className={cn(
                                i % 2 === 0 ? "bg-white" : "bg-slate-50/60",
                                "align-top border-b border-slate-100 last:border-0"
                              )}
                            >
                              <td className="py-2.5 px-4 font-semibold text-slate-800 whitespace-nowrap w-52 text-xs">
                                {row.label}
                              </td>
                              <td className="py-2.5 px-4 font-mono text-xs text-slate-600">
                                {row.formula}
                              </td>
                              <td className="py-2.5 px-4 w-44">
                                {badge && (
                                  <span className={cn(
                                    "inline-block text-[11px] border rounded-full px-2 py-0.5 font-semibold whitespace-nowrap",
                                    badge.cls
                                  )}>
                                    {badge.label}
                                  </span>
                                )}
                                {row.source && (
                                  <div className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                                    {row.source}
                                  </div>
                                )}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
