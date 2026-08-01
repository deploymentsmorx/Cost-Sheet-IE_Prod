import { useEffect, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { normsApi } from "../../api/norms"
import type { CostOverheadParam, NormLibraryDetail } from "../../types/norms"
import { Button } from "../ui/button"
import { cn, fmt, fmtDate } from "../../lib/utils"

interface Props {
  detail: NormLibraryDetail
  readOnly: boolean
}

const CARDS: Array<{ key: CostOverheadParam["applies_to"]; label: string }> = [
  { key: "raw_material",  label: "Raw Material" },
  { key: "bought_out",    label: "Bought-Out Parts" },
  { key: "process_cost",  label: "Process Cost" },
]

type ValueMap = Record<number, string>  // param id -> value string

export function OverheadParams({ detail, readOnly }: Props) {
  const qc = useQueryClient()
  const { library: version, overhead_params } = detail

  const [valueMap, setValueMap] = useState<ValueMap>(() =>
    Object.fromEntries(overhead_params.map(p => [p.id, fmt(p.param_value)]))
  )
  const [dirty, setDirty] = useState(false)
  const [addingCard, setAddingCard] = useState<string | null>(null)
  const [addName, setAddName]   = useState("")
  const [addValue, setAddValue] = useState("")

  useEffect(() => {
    setValueMap(Object.fromEntries(overhead_params.map(p => [p.id, fmt(p.param_value)])))
    setDirty(false)
  }, [detail])

  const saveMutation = useMutation({
    mutationFn: () =>
      normsApi.updateOverheadParams(version.id,
        overhead_params.map(p => ({ id: p.id, param_value: valueMap[p.id] ?? null }))
      ),
    onSuccess: data => { qc.setQueryData(["library", version.id], data); setDirty(false); toast.success("Overhead parameters saved") },
    onError: (e: Error) => toast.error(e.message),
  })

  const addMutation = useMutation({
    mutationFn: (appliesTo: string) => normsApi.addOverheadParam(version.id, {
      applies_to: appliesTo,
      param_name: addName.trim(),
      param_value: addValue || undefined,
    }),
    onSuccess: data => {
      qc.setQueryData(["library", version.id], data)
      setAddingCard(null)
      setAddName("")
      setAddValue("")
      toast.success(`Parameter "${addName}" added`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {CARDS.map(card => {
          const params = overhead_params.filter(p => p.applies_to === card.key)
          return (
            <div key={card.key} className="rounded-lg border bg-card p-4 space-y-3">
              <h3 className="font-semibold text-sm border-b pb-2">{card.label}</h3>

              {params.map(p => (
                <div key={p.id}>
                  <div className="flex items-center justify-between gap-2">
                    <label className="text-sm text-muted-foreground shrink-0">{p.param_name}</label>
                    <div className="flex items-center gap-1">
                      <input
                        type="number" step="0.01" min="0"
                        value={valueMap[p.id] ?? ""}
                        disabled={readOnly}
                        onChange={e => { setValueMap(prev => ({ ...prev, [p.id]: e.target.value })); setDirty(true) }}
                        className={cn(
                          "w-20 text-right border rounded px-2 py-1 text-sm",
                          "focus:outline-none focus:ring-1 focus:ring-ring",
                          "disabled:bg-muted disabled:text-muted-foreground"
                        )}
                      />
                      <span className="text-sm text-muted-foreground">%</span>
                    </div>
                  </div>
                  <div className="text-[11px] text-muted-foreground text-right">
                    Last amended: {fmtDate(p.updated_at)}
                  </div>
                </div>
              ))}

              {/* Add parameter inline form */}
              {!readOnly && addingCard === card.key && (
                <div className="border-t pt-3 space-y-2">
                  <input
                    autoFocus
                    placeholder="Parameter name"
                    value={addName}
                    onChange={e => setAddName(e.target.value)}
                    className="border rounded px-2 py-1.5 text-sm w-full"
                  />
                  <div className="flex items-center gap-2">
                    <input
                      type="number" step="0.01" min="0" placeholder="0.00"
                      value={addValue}
                      onChange={e => setAddValue(e.target.value)}
                      className="border rounded px-2 py-1.5 text-sm w-24 text-right"
                    />
                    <span className="text-sm text-muted-foreground">%</span>
                    <Button size="sm" onClick={() => addMutation.mutate(card.key)}
                      disabled={!addName || addMutation.isPending}>
                      {addMutation.isPending ? "…" : "Add"}
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => { setAddingCard(null); setAddName(""); setAddValue("") }}>✕</Button>
                  </div>
                </div>
              )}

              {!readOnly && addingCard !== card.key && (
                <button
                  onClick={() => { setAddingCard(card.key); setAddName(""); setAddValue("") }}
                  className="text-xs text-primary hover:underline w-full text-left pt-1 border-t"
                >
                  + Add parameter
                </button>
              )}
            </div>
          )
        })}
      </div>

      {!readOnly && (
        <div className="flex justify-end">
          <Button onClick={() => saveMutation.mutate()} disabled={!dirty || saveMutation.isPending} size="sm">
            {saveMutation.isPending ? "Saving…" : "Save Overhead Params"}
          </Button>
        </div>
      )}
    </div>
  )
}
