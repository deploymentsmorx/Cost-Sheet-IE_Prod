import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Check, Trash2, ArrowRightCircle } from "lucide-react"
import { normsApi } from "../../api/norms"
import type { NormLibraryDetail } from "../../types/norms"
import { Button } from "../ui/button"
import { fmt, fmtDate } from "../../lib/utils"

const BANDS = ["<10mm", "12mm", ">12-19mm", "20mm", ">20-40mm", ">40-63mm", "80mm"]

const inputCls = "border rounded px-2 py-1 text-sm w-full text-right focus:outline-none focus:ring-1 focus:ring-ring"

interface Props {
  detail: NormLibraryDetail
  readOnly: boolean
}

interface RowEdit {
  basic_price_per_tonne: string
  ust_amount: string
  trimming_amount: string
  normalising_amount: string
  trader_transport_constant: string
}

const emptyAdd = {
  grade_id: "" as number | "",
  thickness_band: "<10mm",
  basic_price_per_tonne: "0",
  ust_amount: "0",
  trimming_amount: "0",
  normalising_amount: "0",
  trader_transport_constant: "0",
}

export function SteelPriceBuildUp({ detail, readOnly }: Props) {
  const qc = useQueryClient()
  const { library: version, steel_price_buildups, material_grades } = detail

  const gradeName = (id: number) => material_grades.find(g => g.id === id)?.name ?? `#${id}`

  const [edits, setEdits] = useState<Record<number, RowEdit>>({})
  const [adding, setAdding] = useState(false)
  const [addForm, setAddForm] = useState(emptyAdd)

  function rowValue(id: number, field: keyof RowEdit, fallback: string) {
    return edits[id]?.[field] ?? fallback
  }
  function setRowValue(id: number, field: keyof RowEdit, value: string, fallback: RowEdit) {
    setEdits(prev => ({ ...prev, [id]: { ...fallback, ...prev[id], [field]: value } }))
  }

  const saveMutation = useMutation({
    mutationFn: (id: number) => normsApi.updateSteelBuildup(version.id, id, edits[id]),
    onSuccess: (data, id) => {
      qc.setQueryData(["library", version.id], data)
      setEdits(prev => { const n = { ...prev }; delete n[id]; return n })
      toast.success("Build-up saved")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => normsApi.deleteSteelBuildup(version.id, id),
    onSuccess: data => { qc.setQueryData(["library", version.id], data); toast.success("Build-up removed") },
    onError: (e: Error) => toast.error(e.message),
  })

  const applyMutation = useMutation({
    mutationFn: (id: number) => normsApi.applySteelBuildupToRm(version.id, id),
    onSuccess: data => { qc.setQueryData(["library", version.id], data); toast.success("Applied to RM price matrix") },
    onError: (e: Error) => toast.error(e.message),
  })

  const addMutation = useMutation({
    mutationFn: () => normsApi.addSteelBuildup(version.id, {
      grade_id: addForm.grade_id as number,
      thickness_band: addForm.thickness_band,
      basic_price_per_tonne: addForm.basic_price_per_tonne,
      ust_amount: addForm.ust_amount,
      trimming_amount: addForm.trimming_amount,
      normalising_amount: addForm.normalising_amount,
      trader_transport_constant: addForm.trader_transport_constant,
    }),
    onSuccess: data => {
      qc.setQueryData(["library", version.id], data)
      setAdding(false)
      setAddForm(emptyAdd)
      toast.success("Steel price build-up added")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Basic price/tonne + UST + trimming + normalising + trader/transport constant, auto-converted to Rs/kg.
        Use "Apply to RM" to push the computed rate into the RM Price Matrix for that grade + thickness band.
      </p>
      <div className="overflow-x-auto rounded border">
        <table className="text-sm w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="border-b px-3 py-2 text-left font-semibold">Grade</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold">Band</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-28">Basic/Tonne</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-24">UST</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-24">Trimming</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-24">Normalising</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-28">Trader/Transport</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-24 bg-emerald-50">Rs/Kg</th>
              <th className="border-b border-l px-3 py-2 w-24"></th>
            </tr>
          </thead>
          <tbody>
            {steel_price_buildups.map((b, i) => {
              const dirty = !!edits[b.id]
              const fallback: RowEdit = {
                basic_price_per_tonne: fmt(b.basic_price_per_tonne),
                ust_amount: fmt(b.ust_amount),
                trimming_amount: fmt(b.trimming_amount),
                normalising_amount: fmt(b.normalising_amount),
                trader_transport_constant: fmt(b.trader_transport_constant),
              }
              return (
                <tr key={b.id} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                  <td className="border-b px-3 py-1.5">{gradeName(b.grade_id)}</td>
                  <td className="border-b border-l px-3 py-1.5 text-xs">{b.thickness_band}</td>
                  {(["basic_price_per_tonne", "ust_amount", "trimming_amount", "normalising_amount", "trader_transport_constant"] as const).map(field => (
                    <td key={field} className="border-b border-l px-1 py-0.5">
                      <input
                        type="number" step="0.01" min="0"
                        value={rowValue(b.id, field, fallback[field])}
                        disabled={readOnly}
                        onChange={e => setRowValue(b.id, field, e.target.value, fallback)}
                        className={inputCls}
                      />
                    </td>
                  ))}
                  <td className="border-b border-l px-3 py-1.5 text-right font-semibold bg-emerald-50/60">
                    {fmt(b.price_per_kg)}
                  </td>
                  <td className="border-b border-l px-2 py-1.5">
                    <div className="flex items-center justify-end gap-1.5">
                      {!readOnly && dirty && (
                        <button onClick={() => saveMutation.mutate(b.id)} title="Save" className="text-emerald-600 hover:text-emerald-700">
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                      {!readOnly && (
                        <button onClick={() => applyMutation.mutate(b.id)} title="Apply to RM price matrix" className="text-sky-600 hover:text-sky-700">
                          <ArrowRightCircle className="w-4 h-4" />
                        </button>
                      )}
                      {!readOnly && (
                        <button onClick={() => { if (confirm("Remove this build-up?")) deleteMutation.mutate(b.id) }} title="Delete" className="text-red-500 hover:text-red-600">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}

            {steel_price_buildups.length === 0 && !adding && (
              <tr><td colSpan={9} className="px-3 py-4 text-center text-muted-foreground text-xs">No steel price build-ups yet.</td></tr>
            )}

            {!readOnly && adding && (
              <tr className="bg-sky-50 border-b">
                <td className="px-2 py-2">
                  <select value={addForm.grade_id} onChange={e => setAddForm(f => ({ ...f, grade_id: e.target.value === "" ? "" : Number(e.target.value) }))}
                    className="border rounded px-2 py-1 text-sm w-full">
                    <option value="">Grade…</option>
                    {material_grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                  </select>
                </td>
                <td className="border-l px-2 py-2">
                  <select value={addForm.thickness_band} onChange={e => setAddForm(f => ({ ...f, thickness_band: e.target.value }))}
                    className="border rounded px-2 py-1 text-sm w-full">
                    {BANDS.map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                </td>
                {(["basic_price_per_tonne", "ust_amount", "trimming_amount", "normalising_amount", "trader_transport_constant"] as const).map(field => (
                  <td key={field} className="border-l px-1 py-1">
                    <input type="number" step="0.01" min="0" value={addForm[field]}
                      onChange={e => setAddForm(f => ({ ...f, [field]: e.target.value }))}
                      className={inputCls} />
                  </td>
                ))}
                <td className="border-l px-2 py-1 text-center text-muted-foreground text-xs">auto</td>
                <td className="border-l px-2 py-1">
                  <div className="flex gap-1 justify-end">
                    <Button size="sm" onClick={() => addMutation.mutate()} disabled={addForm.grade_id === "" || addMutation.isPending}>
                      {addMutation.isPending ? "…" : "Add"}
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => { setAdding(false); setAddForm(emptyAdd) }}>✕</Button>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!readOnly && !adding && (
        <button onClick={() => setAdding(true)} className="text-xs text-primary hover:underline">
          + Add steel price build-up
        </button>
      )}
      {steel_price_buildups.length > 0 && (
        <p className="text-[11px] text-muted-foreground">
          Last amended: {fmtDate(steel_price_buildups[0]?.updated_at)}
        </p>
      )}
    </div>
  )
}
