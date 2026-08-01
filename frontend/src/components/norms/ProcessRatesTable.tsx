import { useEffect, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { normsApi } from "../../api/norms"
import type { NormLibraryDetail, ProcessRate } from "../../types/norms"
import { Button } from "../ui/button"
import { fmt, fmtDate } from "../../lib/utils"

const UNIT_OPTIONS = ["Rs/Kg", "Rs/Hr", "Rs/mm/meter", "Rs/slant/meter", "Rs/Nos", "Rs/Sqm", "%"]

const GROUP_ORDER = [
  "Material / Cutting",
  "Forming",
  "Drilling",
  "Welding / Finishing",
  "Surface Treatment",
  "Other",
]

interface Props {
  detail: NormLibraryDetail
  readOnly: boolean
}

type RateMap = Record<number, string>

interface AddRowState {
  operation_name: string
  unit: string
  rate: string
}

const emptyAdd: AddRowState = { operation_name: "", unit: "Rs/Hr", rate: "0" }

export function ProcessRatesTable({ detail, readOnly }: Props) {
  const qc = useQueryClient()
  const { library: version, process_rates } = detail

  const [rateMap, setRateMap] = useState<RateMap>(() =>
    Object.fromEntries(process_rates.map(r => [r.id, fmt(r.rate)]))
  )
  const [dirty, setDirty] = useState(false)
  const [addingGroup, setAddingGroup] = useState<string | null>(null)
  const [addForm, setAddForm] = useState<AddRowState>(emptyAdd)

  useEffect(() => {
    setRateMap(Object.fromEntries(process_rates.map(r => [r.id, fmt(r.rate)])))
    setDirty(false)
  }, [detail])

  const saveMutation = useMutation({
    mutationFn: () =>
      normsApi.updateProcessRates(version.id, process_rates.map(r => ({ id: r.id, rate: rateMap[r.id] ?? r.rate }))),
    onSuccess: data => { qc.setQueryData(["library", version.id], data); setDirty(false); toast.success("Process rates saved") },
    onError: (e: Error) => toast.error(e.message),
  })

  const addMutation = useMutation({
    mutationFn: (group: string) => normsApi.addProcessRate(version.id, {
      operation_name: addForm.operation_name.trim(),
      unit: addForm.unit,
      rate: addForm.rate,
      group_label: group,
    }),
    onSuccess: data => {
      qc.setQueryData(["library", version.id], data)
      setAddingGroup(null)
      setAddForm(emptyAdd)
      toast.success("Operation added")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  // Group rates by group_label, preserving GROUP_ORDER
  const grouped = new Map<string, ProcessRate[]>()
  for (const g of GROUP_ORDER) grouped.set(g, [])
  for (const r of process_rates) {
    const label = r.group_label || "Other"
    if (!grouped.has(label)) grouped.set(label, [])
    grouped.get(label)!.push(r)
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded border">
        <table className="text-sm w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="border-b px-3 py-2 text-left font-semibold">Operation</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold w-36">Unit</th>
              <th className="border-b border-l px-3 py-2 text-right font-semibold w-32">Rate</th>
              <th className="border-b border-l px-3 py-2 text-left font-semibold w-36 text-muted-foreground text-xs font-normal">Last Amended</th>
            </tr>
          </thead>
          <tbody>
            {Array.from(grouped.entries()).map(([group, rates]) => (
              <>
                {/* Group header */}
                <tr key={`hdr-${group}`}>
                  <td colSpan={4} className="bg-accent/60 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-accent-foreground border-b">
                    {group}
                  </td>
                </tr>

                {/* Rate rows */}
                {rates.map((r, i) => (
                  <tr key={r.id} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                    <td className="border-b px-3 py-1.5">{r.operation_name}</td>
                    <td className="border-b border-l px-3 py-1.5 text-muted-foreground text-xs">{r.unit}</td>
                    <td className="border-b border-l px-1 py-0.5">
                      <input
                        type="number" step="0.01" min="0"
                        value={rateMap[r.id] ?? ""}
                        disabled={readOnly}
                        onChange={e => { setRateMap(p => ({ ...p, [r.id]: e.target.value })); setDirty(true) }}
                        className="w-full text-right px-2 py-1 rounded text-sm border-0 bg-transparent focus:bg-white focus:outline-none focus:ring-1 focus:ring-ring disabled:text-muted-foreground"
                      />
                    </td>
                    <td className="border-b border-l px-3 py-1.5 text-xs text-muted-foreground whitespace-nowrap">
                      {fmtDate(r.updated_at)}
                    </td>
                  </tr>
                ))}

                {/* Add row inline form */}
                {!readOnly && addingGroup === group && (
                  <tr key={`add-${group}`} className="bg-sky-50 border-b">
                    <td className="px-2 py-2">
                      <input
                        autoFocus
                        placeholder="Operation name"
                        value={addForm.operation_name}
                        onChange={e => setAddForm(p => ({ ...p, operation_name: e.target.value }))}
                        className="border rounded px-2 py-1 text-sm w-full"
                      />
                    </td>
                    <td className="border-l px-2 py-2">
                      <select value={addForm.unit} onChange={e => setAddForm(p => ({ ...p, unit: e.target.value }))}
                        className="border rounded px-2 py-1 text-sm w-full">
                        {UNIT_OPTIONS.map(u => <option key={u} value={u}>{u}</option>)}
                      </select>
                    </td>
                    <td className="border-l px-2 py-2">
                      <input type="number" step="0.01" min="0" placeholder="0.00"
                        value={addForm.rate}
                        onChange={e => setAddForm(p => ({ ...p, rate: e.target.value }))}
                        className="border rounded px-2 py-1 text-sm w-full text-right"
                      />
                    </td>
                    <td className="border-l px-2 py-2">
                      <div className="flex gap-1">
                        <Button size="sm" onClick={() => addMutation.mutate(group)}
                          disabled={!addForm.operation_name || addMutation.isPending}>
                          {addMutation.isPending ? "…" : "Add"}
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => { setAddingGroup(null); setAddForm(emptyAdd) }}>✕</Button>
                      </div>
                    </td>
                  </tr>
                )}

                {/* Add operation button per group */}
                {!readOnly && addingGroup !== group && (
                  <tr key={`btn-${group}`}>
                    <td colSpan={4} className="border-b px-3 py-1">
                      <button
                        onClick={() => { setAddingGroup(group); setAddForm(emptyAdd) }}
                        className="text-xs text-primary hover:underline"
                      >
                        + Add operation to {group}
                      </button>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {!readOnly && (
        <div className="flex justify-end">
          <Button onClick={() => saveMutation.mutate()} disabled={!dirty || saveMutation.isPending} size="sm">
            {saveMutation.isPending ? "Saving…" : "Save Process Rates"}
          </Button>
        </div>
      )}
    </div>
  )
}
