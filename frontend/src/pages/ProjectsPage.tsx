import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { FolderOpen, ChevronRight } from "lucide-react"
import { partsApi } from "../api/parts"
import { clientsApi } from "../api/clients"
import { Button } from "../components/ui/button"
import { cn } from "../lib/utils"
import type { Workbook } from "../types/parts"

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
}

const inputCls = "border border-slate-200 rounded-lg px-3 py-2 text-sm w-full bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
const labelCls = "text-xs font-semibold text-slate-500 mb-1.5 block uppercase tracking-wide"

export function ProjectsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [clientFilter, setClientFilter] = useState<number | "">("")

  const { data: clients = [] } = useQuery({
    queryKey: ["clients"],
    queryFn: () => clientsApi.list(),
  })

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["workbooks", clientFilter],
    queryFn: () => partsApi.listWorkbooks(clientFilter !== "" ? clientFilter : undefined),
  })

  const [creating, setCreating] = useState(false)
  const [name, setName] = useState("")
  const [clientId, setClientId] = useState<number | "">("")
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState("")
  const [editClientId, setEditClientId] = useState<number | "">("")

  const createMutation = useMutation({
    mutationFn: () => partsApi.createWorkbook({ name: name.trim(), client_id: clientId as number }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["workbooks"] })
      setCreating(false); setName(""); setClientId("")
      toast.success("Costing Workbook created")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id }: { id: number }) =>
      partsApi.updateWorkbook(id, {
        name: editName.trim(),
        ...(editClientId !== "" ? { client_id: editClientId as number } : {}),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["workbooks"] })
      setEditingId(null)
      toast.success("Costing Workbook updated")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: partsApi.deleteWorkbook,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["workbooks"] })
      toast.success("Costing Workbook deleted")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  function startEdit(p: Workbook) {
    setEditingId(p.id); setEditName(p.name); setEditClientId(p.client_id ?? "")
  }

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading…</div>
  )

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">

      {/* Page header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Costing Workbooks</h1>
          <p className="text-sm text-slate-500 mt-1">Manage your project workbooks and costsheets</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Client filter */}
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide shrink-0">Client</span>
            <select
              value={clientFilter}
              onChange={e => setClientFilter(e.target.value === "" ? "" : Number(e.target.value))}
              className="text-sm bg-transparent focus:outline-none text-slate-700 font-medium min-w-[160px]"
            >
              <option value="">All clients</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          {!creating && (
            <Button size="sm" onClick={() => setCreating(true)}>
              + New Workbook
            </Button>
          )}
        </div>
      </div>

      {/* Create form */}
      {creating && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60">
            <h2 className="text-sm font-semibold text-slate-900">New Costing Workbook</h2>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Workbook Name *</label>
                <input
                  autoFocus
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g. Metso 2024 RFQ"
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Client *</label>
                <select
                  value={clientId}
                  onChange={e => setClientId(e.target.value === "" ? "" : Number(e.target.value))}
                  className={inputCls}
                >
                  <option value="">Select a client…</option>
                  {clients.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-2 justify-end pt-2 border-t border-slate-100">
              <Button variant="ghost" size="sm" onClick={() => { setCreating(false); setName(""); setClientId("") }}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => createMutation.mutate()}
                disabled={!name.trim() || clientId === "" || createMutation.isPending}
              >
                {createMutation.isPending ? "Creating…" : "Create Workbook"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      {projects.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
            <FolderOpen className="w-7 h-7 text-slate-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 mb-1">No workbooks yet</h3>
          <p className="text-sm text-slate-500 mb-5">
            {clientFilter !== "" ? "No workbooks for this client." : "Create your first costing workbook to get started."}
          </p>
          <Button size="sm" onClick={() => setCreating(true)}>+ New Workbook</Button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Workbook Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Client</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Costsheets</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {projects.map(p => (
                <tr key={p.id} className={cn("hover:bg-slate-50/70 transition-colors", editingId === p.id && "bg-sky-50/30")}>
                  {editingId === p.id ? (
                    <>
                      <td className="px-4 py-2.5">
                        <input
                          autoFocus value={editName} onChange={e => setEditName(e.target.value)}
                          className={inputCls}
                        />
                      </td>
                      <td className="px-4 py-2.5">
                        <select
                          value={editClientId}
                          onChange={e => setEditClientId(e.target.value === "" ? "" : Number(e.target.value))}
                          className={inputCls}
                        >
                          <option value="">— unchanged —</option>
                          {clients.map(c => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2.5 text-center text-slate-400">{p.sheet_count}</td>
                      <td className="px-4 py-2.5 text-slate-400">{fmtDate(p.created_at)}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex gap-1 justify-end">
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>Cancel</Button>
                          <Button size="sm" onClick={() => updateMutation.mutate({ id: p.id })} disabled={!editName.trim() || updateMutation.isPending}>
                            Save
                          </Button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3.5">
                        <button
                          className="font-semibold text-primary hover:text-primary/80 hover:underline text-left flex items-center gap-1.5 group"
                          onClick={() => navigate(`/workbooks/${p.id}/summary`)}
                        >
                          {p.name}
                          <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </button>
                      </td>
                      <td className="px-4 py-3.5 text-slate-500">{p.client_name ?? <span className="text-slate-300">—</span>}</td>
                      <td className="px-4 py-3.5 text-center">
                        <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold">
                          {p.sheet_count}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-slate-400 text-xs">{fmtDate(p.created_at)}</td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1 justify-end">
                          <button
                            onClick={() => startEdit(p)}
                            className="text-xs font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-100 px-2.5 py-1 rounded-md transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            className="text-xs font-medium text-slate-400 hover:text-red-600 hover:bg-red-50 px-2.5 py-1 rounded-md transition-colors"
                            onClick={() => {
                              if (confirm(`Delete costing workbook "${p.name}" and all its costsheets?`))
                                deleteMutation.mutate(p.id)
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
