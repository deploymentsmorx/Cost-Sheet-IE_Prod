import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Layers, ChevronRight, ImagePlus } from "lucide-react"
import { partsApi } from "../api/parts"
import { Button } from "../components/ui/button"
import { cn } from "../lib/utils"
import { API_BASE_URL } from "../lib/apiBase"
import type { CostSheetWithLines } from "../types/parts"

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
}

const inputCls = "border border-slate-200 rounded-lg px-3 py-2 text-sm w-full bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
const labelCls = "text-xs font-semibold text-slate-500 mb-1.5 block uppercase tracking-wide"

export function PartsPage() {
  const { workbookId } = useParams<{ workbookId: string }>()
  const wid = Number(workbookId)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: workbooks = [] } = useQuery({
    queryKey: ["workbooks"],
    queryFn: () => partsApi.listWorkbooks(),
  })
  const workbook = workbooks.find(w => w.id === wid)

  const { data: sheets = [], isLoading } = useQuery({
    queryKey: ["sheets", wid],
    queryFn: () => partsApi.listSheets(wid),
  })

  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ name: "", part_no: "", description: "", drawing_no: "", benchmark_price: "", supply_version: "V1" })

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState({ name: "", part_no: "", description: "", drawing_no: "", benchmark_price: "" })

  const createMutation = useMutation({
    mutationFn: () => partsApi.createSheet(wid, {
      name: form.name.trim(),
      part_no: form.part_no.trim() || undefined,
      description: form.description.trim() || undefined,
      drawing_no: form.drawing_no.trim() || undefined,
      benchmark_price: form.benchmark_price || undefined,
      supply_version: form.supply_version.trim() || "V1",
    }),
    onSuccess: (sheet) => {
      qc.invalidateQueries({ queryKey: ["sheets", wid] })
      qc.invalidateQueries({ queryKey: ["workbooks"] })
      setCreating(false)
      setForm({ name: "", part_no: "", description: "", drawing_no: "", benchmark_price: "", supply_version: "V1" })
      toast.success("Cost sheet created")
      navigate(`/sheets/${sheet.id}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id }: { id: number }) => partsApi.updateSheet(id, {
      name: editForm.name.trim() || undefined,
      part_no: editForm.part_no.trim() || null,
      description: editForm.description.trim() || null,
      drawing_no: editForm.drawing_no.trim() || null,
      benchmark_price: editForm.benchmark_price || null,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheets", wid] })
      setEditingId(null)
      toast.success("Cost sheet updated")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: partsApi.deleteSheet,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheets", wid] })
      qc.invalidateQueries({ queryKey: ["workbooks"] })
      toast.success("Cost sheet deleted")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const uploadImageMutation = useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) => partsApi.uploadImage(id, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sheets", wid] })
      toast.success("Image uploaded")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  function startEdit(s: CostSheetWithLines) {
    setEditingId(s.id)
    setEditForm({
      name: s.name,
      part_no: s.part_no ?? "",
      description: s.description ?? "",
      drawing_no: s.drawing_no ?? "",
      benchmark_price: s.benchmark_price ?? "",
    })
  }

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading…</div>
  )

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm">
        <button onClick={() => navigate("/workbooks")} className="text-slate-500 hover:text-slate-900 transition-colors font-medium">
          Costing Workbooks
        </button>
        <ChevronRight className="w-4 h-4 text-slate-400" />
        <span className="text-slate-900 font-semibold">{workbook?.name ?? `Workbook ${wid}`}</span>
        {workbook?.client_name && <span className="text-slate-400 ml-0.5">— {workbook.client_name}</span>}
      </nav>

      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Cost Sheets</h1>
          <p className="text-sm text-slate-500 mt-1">Each sheet costs one part using this workbook's norm library</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate(`/workbooks/${wid}/summary`)}>
            Summary View
          </Button>
          {!creating && (
            <Button size="sm" onClick={() => setCreating(true)}>+ New Cost Sheet</Button>
          )}
        </div>
      </div>

      {/* Create form */}
      {creating && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60">
            <h2 className="text-sm font-semibold text-slate-900">New Cost Sheet</h2>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className={labelCls}>Name *</label>
                <input
                  autoFocus value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Side Plate LH"
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Part No.</label>
                <input
                  value={form.part_no}
                  onChange={e => setForm(f => ({ ...f, part_no: e.target.value }))}
                  placeholder="e.g. SPC-001"
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Supply Version</label>
                <input
                  value={form.supply_version}
                  onChange={e => setForm(f => ({ ...f, supply_version: e.target.value }))}
                  placeholder="e.g. V1"
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Drawing No.</label>
                <input
                  value={form.drawing_no}
                  onChange={e => setForm(f => ({ ...f, drawing_no: e.target.value }))}
                  placeholder="e.g. DWG-2024-001"
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Benchmark Price (Rs)</label>
                <input
                  type="number" min="0" step="0.01"
                  value={form.benchmark_price}
                  onChange={e => setForm(f => ({ ...f, benchmark_price: e.target.value }))}
                  placeholder="Optional reference price"
                  className={inputCls}
                />
              </div>
            </div>
            <div className="flex gap-2 justify-end pt-2 border-t border-slate-100">
              <Button variant="ghost" size="sm" onClick={() => { setCreating(false); setForm({ name: "", part_no: "", description: "", drawing_no: "", benchmark_price: "", supply_version: "V1" }) }}>
                Cancel
              </Button>
              <Button size="sm" onClick={() => createMutation.mutate()} disabled={!form.name.trim() || createMutation.isPending}>
                {createMutation.isPending ? "Creating…" : "Create & Open"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      {sheets.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
            <Layers className="w-7 h-7 text-slate-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 mb-1">No cost sheets yet</h3>
          <p className="text-sm text-slate-500 mb-5">Create a cost sheet to start costing a part</p>
          <Button size="sm" onClick={() => setCreating(true)}>+ New Cost Sheet</Button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider w-16">Image</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Part No.</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Drawing No.</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Version</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Benchmark (Rs)</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sheets.map(s => (
                <tr key={s.id} className={cn("hover:bg-slate-50/60 transition-colors align-top", editingId === s.id && "bg-sky-50/30")}>
                  <td className="px-4 py-2.5">
                    <label className="block w-10 h-10 rounded-md border border-slate-200 bg-slate-50 overflow-hidden cursor-pointer hover:border-primary/50 transition-colors relative group">
                      {s.image_url ? (
                        <img src={API_BASE_URL + s.image_url} alt={s.name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-300">
                          <ImagePlus className="w-4 h-4" />
                        </div>
                      )}
                      <input
                        type="file" accept="image/png,image/jpeg,image/webp,image/gif"
                        className="hidden"
                        onChange={e => {
                          const file = e.target.files?.[0]
                          if (file) uploadImageMutation.mutate({ id: s.id, file })
                          e.target.value = ""
                        }}
                      />
                    </label>
                  </td>
                  {editingId === s.id ? (
                    <>
                      <td className="px-4 py-2.5">
                        <input autoFocus value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} className={inputCls} />
                      </td>
                      <td className="px-4 py-2.5">
                        <input value={editForm.part_no} onChange={e => setEditForm(f => ({ ...f, part_no: e.target.value }))} className={inputCls} />
                      </td>
                      <td className="px-4 py-2.5">
                        <input value={editForm.drawing_no} onChange={e => setEditForm(f => ({ ...f, drawing_no: e.target.value }))} className={inputCls} />
                      </td>
                      <td className="px-4 py-2.5 text-slate-400 text-xs">{s.supply_version}</td>
                      <td className="px-4 py-2.5">
                        <input type="number" min="0" step="0.01" value={editForm.benchmark_price} onChange={e => setEditForm(f => ({ ...f, benchmark_price: e.target.value }))} className={cn(inputCls, "text-right")} />
                      </td>
                      <td className="px-4 py-2.5 text-slate-400 text-xs">{fmtDate(s.created_at)}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex gap-1 justify-end">
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>Cancel</Button>
                          <Button size="sm" onClick={() => updateMutation.mutate({ id: s.id })} disabled={!editForm.name.trim() || updateMutation.isPending}>Save</Button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3.5">
                        <button
                          onClick={() => navigate(`/sheets/${s.id}`)}
                          className="font-semibold text-primary hover:text-primary/80 hover:underline text-left"
                        >
                          {s.name}
                        </button>
                      </td>
                      <td className="px-4 py-3.5 text-slate-500 font-mono text-xs">{s.part_no ?? <span className="text-slate-300">—</span>}</td>
                      <td className="px-4 py-3.5 text-slate-400 text-xs font-mono">{s.drawing_no ?? <span className="text-slate-300">—</span>}</td>
                      <td className="px-4 py-3.5">
                        <span className="inline-flex items-center gap-0.5 text-xs bg-sky-50 text-sky-700 border border-sky-200 rounded-full px-2.5 py-0.5 font-medium">
                          {s.supply_version}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-right text-slate-600 tabular-nums">
                        {s.benchmark_price
                          ? <span className="font-medium">Rs {Number(s.benchmark_price).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                          : <span className="text-slate-300">—</span>
                        }
                      </td>
                      <td className="px-4 py-3.5 text-slate-400 text-xs">{fmtDate(s.created_at)}</td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1 justify-end">
                          <button
                            onClick={() => startEdit(s)}
                            className="text-xs font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-100 px-2.5 py-1 rounded-md transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            className="text-xs font-medium text-slate-400 hover:text-red-600 hover:bg-red-50 px-2.5 py-1 rounded-md transition-colors"
                            onClick={() => {
                              if (confirm(`Delete cost sheet "${s.name}"? All costing lines and results will be removed.`))
                                deleteMutation.mutate(s.id)
                            }}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
