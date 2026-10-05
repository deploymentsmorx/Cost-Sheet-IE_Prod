import { Fragment, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Check, Trash2 } from "lucide-react"
import { normsApi } from "../../api/norms"
import type { NormLibraryDetail, SectionCategory } from "../../types/norms"
import { Button } from "../ui/button"
import { fmt, fmtDate } from "../../lib/utils"

const CATEGORY_LABELS: Record<SectionCategory, string> = {
  channel: "Channel (ISMC/UPN)",
  angle: "Angle (ISA)",
  round_bar: "Round Bar",
  square_bar: "Square Bar",
  flat_bar: "Flat Bar",
  pipe: "Pipe",
}
const CATEGORIES = Object.keys(CATEGORY_LABELS) as SectionCategory[]

const inputCls = "border rounded px-2 py-1 text-sm w-full text-right focus:outline-none focus:ring-1 focus:ring-ring"

interface Props {
  detail: NormLibraryDetail
  readOnly: boolean
}

interface RowEdit { kg_per_m: string; rate_per_kg: string }

const emptyAdd = { category: "channel" as SectionCategory, designation: "", kg_per_m: "0", rate_per_kg: "0" }

export function SectionCatalogTable({ detail, readOnly }: Props) {
  const qc = useQueryClient()
  const { library: version, section_catalog_items } = detail

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
    mutationFn: (id: number) => normsApi.updateSectionCatalogItem(version.id, id, edits[id]),
    onSuccess: (data, id) => {
      qc.setQueryData(["library", version.id], data)
      setEdits(prev => { const n = { ...prev }; delete n[id]; return n })
      toast.success("Saved")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => normsApi.deleteSectionCatalogItem(version.id, id),
    onSuccess: data => { qc.setQueryData(["library", version.id], data); toast.success("Removed") },
    onError: (e: Error) => toast.error(e.message),
  })

  const addMutation = useMutation({
    mutationFn: () => normsApi.addSectionCatalogItem(version.id, {
      category: addForm.category,
      designation: addForm.designation.trim(),
      kg_per_m: addForm.kg_per_m,
      rate_per_kg: addForm.rate_per_kg,
    }),
    onSuccess: data => {
      qc.setQueryData(["library", version.id], data)
      setAdding(false)
      setAddForm(emptyAdd)
      toast.success(`Added "${addForm.designation}"`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  // Group by category
  const grouped = new Map<SectionCategory, typeof section_catalog_items>()
  for (const c of CATEGORIES) grouped.set(c, [])
  for (const item of section_catalog_items) {
    if (!grouped.has(item.category)) grouped.set(item.category, [])
    grouped.get(item.category)!.push(item)
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Channels, angles, round/square/flat bars and pipes — kg/m and rate/kg, with rate/m computed automatically.
      </p>
      <div className="overflow-x-auto rounded border">
        <table className="text-sm w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="border-b px-3 py-2 text-left font-semibold">Designation</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-28">kg/m</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-28">Rate/kg</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-28 bg-emerald-50">Rate/m</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold w-32 text-muted-foreground text-xs font-normal">Last Amended</th>
              <th className="border-b border-l px-3 py-2 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {CATEGORIES.map(cat => {
              const items = grouped.get(cat) ?? []
              return (
                <Fragment key={cat}>
                  <tr key={`hdr-${cat}`}>
                    <td colSpan={6} className="bg-accent/60 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-accent-foreground border-b">
                      {CATEGORY_LABELS[cat]}
                    </td>
                  </tr>
                  {items.map((item, i) => {
                    const dirty = !!edits[item.id]
                    const fallback: RowEdit = { kg_per_m: fmt(item.kg_per_m), rate_per_kg: fmt(item.rate_per_kg) }
                    return (
                      <tr key={item.id} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                        <td className="border-b px-3 py-1.5">{item.designation}</td>
                        <td className="border-b border-l px-1 py-0.5">
                          <input type="number" step="0.0001" min="0" value={rowValue(item.id, "kg_per_m", fallback.kg_per_m)}
                            disabled={readOnly} onChange={e => setRowValue(item.id, "kg_per_m", e.target.value, fallback)}
                            className={inputCls} />
                        </td>
                        <td className="border-b border-l px-1 py-0.5">
                          <input type="number" step="0.01" min="0" value={rowValue(item.id, "rate_per_kg", fallback.rate_per_kg)}
                            disabled={readOnly} onChange={e => setRowValue(item.id, "rate_per_kg", e.target.value, fallback)}
                            className={inputCls} />
                        </td>
                        <td className="border-b border-l px-3 py-1.5 text-right font-semibold bg-emerald-50/60">{fmt(item.rate_per_m)}</td>
                        <td className="border-b border-l px-3 py-1.5 text-xs text-muted-foreground whitespace-nowrap">{fmtDate(item.updated_at)}</td>
                        <td className="border-b border-l px-2 py-1.5">
                          <div className="flex items-center justify-end gap-1.5">
                            {!readOnly && dirty && (
                              <button onClick={() => saveMutation.mutate(item.id)} title="Save" className="text-emerald-600 hover:text-emerald-700">
                                <Check className="w-4 h-4" />
                              </button>
                            )}
                            {!readOnly && (
                              <button onClick={() => { if (confirm(`Remove "${item.designation}"?`)) deleteMutation.mutate(item.id) }}
                                title="Delete" className="text-red-500 hover:text-red-600">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                  {!readOnly && adding && addForm.category === cat && (
                    <tr className="bg-sky-50 border-b">
                      <td className="px-2 py-2">
                        <input autoFocus placeholder="e.g. ISMC 100" value={addForm.designation}
                          onChange={e => setAddForm(f => ({ ...f, designation: e.target.value }))}
                          className="border rounded px-2 py-1 text-sm w-full" />
                      </td>
                      <td className="border-l px-1 py-1">
                        <input type="number" step="0.0001" min="0" value={addForm.kg_per_m}
                          onChange={e => setAddForm(f => ({ ...f, kg_per_m: e.target.value }))} className={inputCls} />
                      </td>
                      <td className="border-l px-1 py-1">
                        <input type="number" step="0.01" min="0" value={addForm.rate_per_kg}
                          onChange={e => setAddForm(f => ({ ...f, rate_per_kg: e.target.value }))} className={inputCls} />
                      </td>
                      <td className="border-l px-2 py-1 text-center text-muted-foreground text-xs">auto</td>
                      <td className="border-l px-2 py-1"></td>
                      <td className="border-l px-2 py-1">
                        <div className="flex gap-1 justify-end">
                          <Button size="sm" onClick={() => addMutation.mutate()}
                            disabled={!addForm.designation.trim() || addMutation.isPending}>
                            {addMutation.isPending ? "…" : "Add"}
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => { setAdding(false); setAddForm(emptyAdd) }}>✕</Button>
                        </div>
                      </td>
                    </tr>
                  )}
                  {!readOnly && !(adding && addForm.category === cat) && (
                    <tr>
                      <td colSpan={6} className="border-b px-3 py-1">
                        <button onClick={() => { setAdding(true); setAddForm({ ...emptyAdd, category: cat }) }}
                          className="text-xs text-primary hover:underline">
                          + Add to {CATEGORY_LABELS[cat]}
                        </button>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
