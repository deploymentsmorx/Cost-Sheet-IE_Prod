import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Trash2 } from "lucide-react"
import { normsApi } from "../../api/norms"
import type { NormLibraryDetail } from "../../types/norms"
import { Button } from "../ui/button"
import { fmtDate } from "../../lib/utils"

interface Props {
  detail: NormLibraryDetail
  readOnly: boolean
}

const emptyAdd = { customer_spec: "", material_grade_id: "" as number | "", notes: "" }

export function GradeEquivalenceTable({ detail, readOnly }: Props) {
  const qc = useQueryClient()
  const { library: version, grade_equivalences, material_grades } = detail
  const gradeName = (id: number) => material_grades.find(g => g.id === id)?.name ?? `#${id}`

  const [adding, setAdding] = useState(false)
  const [addForm, setAddForm] = useState(emptyAdd)

  const addMutation = useMutation({
    mutationFn: () => normsApi.addGradeEquivalence(version.id, {
      customer_spec: addForm.customer_spec.trim(),
      material_grade_id: addForm.material_grade_id as number,
      notes: addForm.notes.trim() || undefined,
    }),
    onSuccess: data => {
      qc.setQueryData(["library", version.id], data)
      setAdding(false)
      setAddForm(emptyAdd)
      toast.success(`Mapped "${addForm.customer_spec}"`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => normsApi.deleteGradeEquivalence(version.id, id),
    onSuccess: data => { qc.setQueryData(["library", version.id], data); toast.success("Mapping removed") },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Map a customer's material spec to its Indian equivalent, so the line editor can auto-resolve the grade from the spec instead of a manual lookup.
      </p>
      <div className="overflow-x-auto rounded border">
        <table className="text-sm w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="border-b px-3 py-2 text-left font-semibold w-48">Customer Spec</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold w-56">Indian Equivalent</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold">Notes</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold w-36 text-muted-foreground text-xs font-normal">Last Amended</th>
              <th className="border-b border-l px-3 py-2 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {grade_equivalences.map((g, i) => (
              <tr key={g.id} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                <td className="border-b px-3 py-1.5 font-mono text-xs">{g.customer_spec}</td>
                <td className="border-b border-l px-3 py-1.5">{gradeName(g.material_grade_id)}</td>
                <td className="border-b border-l px-3 py-1.5 text-muted-foreground text-xs">{g.notes ?? "—"}</td>
                <td className="border-b border-l px-3 py-1.5 text-xs text-muted-foreground whitespace-nowrap">{fmtDate(g.updated_at)}</td>
                <td className="border-b border-l px-2 py-1.5 text-center">
                  {!readOnly && (
                    <button onClick={() => { if (confirm(`Remove mapping for "${g.customer_spec}"?`)) deleteMutation.mutate(g.id) }}
                      title="Delete" className="text-red-500 hover:text-red-600">
                      <Trash2 className="w-4 h-4 inline" />
                    </button>
                  )}
                </td>
              </tr>
            ))}

            {grade_equivalences.length === 0 && !adding && (
              <tr><td colSpan={5} className="px-3 py-4 text-center text-muted-foreground text-xs">No grade equivalences mapped yet.</td></tr>
            )}

            {!readOnly && adding && (
              <tr className="bg-sky-50 border-b">
                <td className="px-2 py-2">
                  <input autoFocus placeholder="e.g. S235J2" value={addForm.customer_spec}
                    onChange={e => setAddForm(f => ({ ...f, customer_spec: e.target.value }))}
                    className="border rounded px-2 py-1 text-sm w-full" />
                </td>
                <td className="border-l px-2 py-2">
                  <select value={addForm.material_grade_id}
                    onChange={e => setAddForm(f => ({ ...f, material_grade_id: e.target.value === "" ? "" : Number(e.target.value) }))}
                    className="border rounded px-2 py-1 text-sm w-full">
                    <option value="">Select grade…</option>
                    {material_grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                  </select>
                </td>
                <td className="border-l px-2 py-2">
                  <input placeholder="Optional notes" value={addForm.notes}
                    onChange={e => setAddForm(f => ({ ...f, notes: e.target.value }))}
                    className="border rounded px-2 py-1 text-sm w-full" />
                </td>
                <td className="border-l px-2 py-2"></td>
                <td className="border-l px-2 py-2">
                  <div className="flex gap-1 justify-end">
                    <Button size="sm" onClick={() => addMutation.mutate()}
                      disabled={!addForm.customer_spec.trim() || addForm.material_grade_id === "" || addMutation.isPending}>
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
          + Add grade equivalence
        </button>
      )}
    </div>
  )
}
