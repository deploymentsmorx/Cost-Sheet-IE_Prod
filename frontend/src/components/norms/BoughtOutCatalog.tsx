import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Check, Trash2 } from "lucide-react"
import { normsApi } from "../../api/norms"
import type { NormLibraryDetail } from "../../types/norms"
import { Button } from "../ui/button"
import { fmt, fmtDate } from "../../lib/utils"

const inputCls = "border rounded px-2 py-1 text-sm w-full text-right focus:outline-none focus:ring-1 focus:ring-ring"

interface Props {
  detail: NormLibraryDetail
  readOnly: boolean
}

interface RowEdit { unit_weight_kg: string; rate: string }

const emptyAdd = { name: "", category: "", unit_weight_kg: "0", rate: "0" }

export function BoughtOutCatalog({ detail, readOnly }: Props) {
  const qc = useQueryClient()
  const { library: version, bo_catalog_items } = detail

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
    mutationFn: (id: number) => normsApi.updateBoCatalogItem(version.id, id, edits[id]),
    onSuccess: (data, id) => {
      qc.setQueryData(["library", version.id], data)
      setEdits(prev => { const n = { ...prev }; delete n[id]; return n })
      toast.success("Saved")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => normsApi.deleteBoCatalogItem(version.id, id),
    onSuccess: data => { qc.setQueryData(["library", version.id], data); toast.success("Removed") },
    onError: (e: Error) => toast.error(e.message),
  })

  const addMutation = useMutation({
    mutationFn: () => normsApi.addBoCatalogItem(version.id, {
      name: addForm.name.trim(),
      category: addForm.category.trim() || undefined,
      unit_weight_kg: addForm.unit_weight_kg || undefined,
      rate: addForm.rate,
    }),
    onSuccess: data => {
      qc.setQueryData(["library", version.id], data)
      setAdding(false)
      setAddForm(emptyAdd)
      toast.success(`Added "${addForm.name}"`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Reusable bought-out item master — nuts, bolts, washers, bushes. Pick from this list when adding BO items to a cost sheet instead of retyping rates each time.
      </p>
      <div className="overflow-x-auto rounded border">
        <table className="text-sm w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="border-b px-3 py-2 text-left font-semibold">Name</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold w-36">Category</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-28">Weight (kg)</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-28">Rate</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold w-32 text-muted-foreground text-xs font-normal">Last Amended</th>
              <th className="border-b border-l px-3 py-2 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {bo_catalog_items.map((item, i) => {
              const dirty = !!edits[item.id]
              const fallback: RowEdit = { unit_weight_kg: item.unit_weight_kg ? fmt(item.unit_weight_kg) : "", rate: fmt(item.rate) }
              return (
                <tr key={item.id} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                  <td className="border-b px-3 py-1.5">{item.name}</td>
                  <td className="border-b border-l px-3 py-1.5 text-muted-foreground text-xs">{item.category ?? "—"}</td>
                  <td className="border-b border-l px-1 py-0.5">
                    <input type="number" step="0.0001" min="0" value={rowValue(item.id, "unit_weight_kg", fallback.unit_weight_kg)}
                      disabled={readOnly} onChange={e => setRowValue(item.id, "unit_weight_kg", e.target.value, fallback)}
                      className={inputCls} />
                  </td>
                  <td className="border-b border-l px-1 py-0.5">
                    <input type="number" step="0.01" min="0" value={rowValue(item.id, "rate", fallback.rate)}
                      disabled={readOnly} onChange={e => setRowValue(item.id, "rate", e.target.value, fallback)}
                      className={inputCls} />
                  </td>
                  <td className="border-b border-l px-3 py-1.5 text-xs text-muted-foreground whitespace-nowrap">{fmtDate(item.updated_at)}</td>
                  <td className="border-b border-l px-2 py-1.5">
                    <div className="flex items-center justify-end gap-1.5">
                      {!readOnly && dirty && (
                        <button onClick={() => saveMutation.mutate(item.id)} title="Save" className="text-emerald-600 hover:text-emerald-700">
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                      {!readOnly && (
                        <button onClick={() => { if (confirm(`Remove "${item.name}"?`)) deleteMutation.mutate(item.id) }}
                          title="Delete" className="text-red-500 hover:text-red-600">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}

            {bo_catalog_items.length === 0 && !adding && (
              <tr><td colSpan={6} className="px-3 py-4 text-center text-muted-foreground text-xs">No bought-out items yet.</td></tr>
            )}

            {!readOnly && adding && (
              <tr className="bg-sky-50 border-b">
                <td className="px-2 py-2">
                  <input autoFocus placeholder="e.g. M10 Hex Bolt" value={addForm.name}
                    onChange={e => setAddForm(f => ({ ...f, name: e.target.value }))}
                    className="border rounded px-2 py-1 text-sm w-full" />
                </td>
                <td className="border-l px-2 py-2">
                  <input placeholder="e.g. Fastener" value={addForm.category}
                    onChange={e => setAddForm(f => ({ ...f, category: e.target.value }))}
                    className="border rounded px-2 py-1 text-sm w-full" />
                </td>
                <td className="border-l px-1 py-1">
                  <input type="number" step="0.0001" min="0" value={addForm.unit_weight_kg}
                    onChange={e => setAddForm(f => ({ ...f, unit_weight_kg: e.target.value }))} className={inputCls} />
                </td>
                <td className="border-l px-1 py-1">
                  <input type="number" step="0.01" min="0" value={addForm.rate}
                    onChange={e => setAddForm(f => ({ ...f, rate: e.target.value }))} className={inputCls} />
                </td>
                <td className="border-l px-2 py-1"></td>
                <td className="border-l px-2 py-1">
                  <div className="flex gap-1 justify-end">
                    <Button size="sm" onClick={() => addMutation.mutate()}
                      disabled={!addForm.name.trim() || addMutation.isPending}>
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
          + Add bought-out item
        </button>
      )}
    </div>
  )
}
