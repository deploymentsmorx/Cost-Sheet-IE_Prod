import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Users } from "lucide-react"
import { clientsApi } from "../api/clients"
import { Button } from "../components/ui/button"
import { cn } from "../lib/utils"
import type { Client } from "../types/clients"

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
}

const inputCls = "border border-slate-200 rounded-lg px-3 py-2 text-sm w-full bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
const labelCls = "text-xs font-semibold text-slate-500 mb-1.5 block uppercase tracking-wide"

export function ClientsPage() {
  const qc = useQueryClient()

  const { data: clients = [], isLoading } = useQuery({
    queryKey: ["clients"],
    queryFn: () => clientsApi.list(),
  })

  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState("")

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState("")

  const createMutation = useMutation({
    mutationFn: () => clientsApi.create(newName.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] })
      setCreating(false)
      setNewName("")
      toast.success("Client created")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id }: { id: number }) => clientsApi.update(id, editName.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] })
      setEditingId(null)
      toast.success("Client updated")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteMutation = useMutation({
    mutationFn: clientsApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] })
      toast.success("Client deleted")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  function startEdit(c: Client) {
    setEditingId(c.id)
    setEditName(c.name)
  }

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading…</div>
  )

  return (
    <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Clients</h1>
          <p className="text-sm text-slate-500 mt-1">Each client gets their own norm library and costing workbooks</p>
        </div>
        {!creating && (
          <Button size="sm" onClick={() => setCreating(true)}>+ New Client</Button>
        )}
      </div>

      {/* Create form */}
      {creating && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60">
            <h2 className="text-sm font-semibold text-slate-900">New Client</h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className={labelCls}>Client Name *</label>
              <input
                autoFocus
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && newName.trim()) createMutation.mutate() }}
                placeholder="e.g. Metso India"
                className={inputCls}
              />
            </div>
            <div className="flex gap-2 justify-end pt-2 border-t border-slate-100">
              <Button variant="ghost" size="sm" onClick={() => { setCreating(false); setNewName("") }}>Cancel</Button>
              <Button size="sm" onClick={() => createMutation.mutate()} disabled={!newName.trim() || createMutation.isPending}>
                {createMutation.isPending ? "Creating…" : "Create Client"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      {clients.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
            <Users className="w-7 h-7 text-slate-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 mb-1">No clients yet</h3>
          <p className="text-sm text-slate-500 mb-5">Create a client to start setting up their norm library and workbooks</p>
          <Button size="sm" onClick={() => setCreating(true)}>+ New Client</Button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Client Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {clients.map(c => (
                <tr key={c.id} className={cn("hover:bg-slate-50/70 transition-colors", editingId === c.id && "bg-sky-50/30")}>
                  {editingId === c.id ? (
                    <>
                      <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">#{c.id}</td>
                      <td className="px-4 py-2.5">
                        <input
                          autoFocus value={editName}
                          onChange={e => setEditName(e.target.value)}
                          onKeyDown={e => {
                            if (e.key === "Enter" && editName.trim()) updateMutation.mutate({ id: c.id })
                            if (e.key === "Escape") setEditingId(null)
                          }}
                          className={inputCls}
                        />
                      </td>
                      <td className="px-4 py-2.5 text-slate-400 text-xs">{fmtDate(c.created_at)}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex gap-1 justify-end">
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>Cancel</Button>
                          <Button size="sm" onClick={() => updateMutation.mutate({ id: c.id })} disabled={!editName.trim() || updateMutation.isPending}>Save</Button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3.5 text-slate-400 font-mono text-xs">#{c.id}</td>
                      <td className="px-4 py-3.5 font-semibold text-slate-900">{c.name}</td>
                      <td className="px-4 py-3.5 text-slate-400 text-xs">{fmtDate(c.created_at)}</td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1 justify-end">
                          <button
                            onClick={() => startEdit(c)}
                            className="text-xs font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-100 px-2.5 py-1 rounded-md transition-colors"
                          >Edit</button>
                          <button
                            className="text-xs font-medium text-slate-400 hover:text-red-600 hover:bg-red-50 px-2.5 py-1 rounded-md transition-colors"
                            onClick={() => {
                              if (confirm(`Delete client "${c.name}"?\n\nThis will permanently delete ALL associated norm libraries, costing workbooks, and their sheets. This cannot be undone.`))
                                deleteMutation.mutate(c.id)
                            }}
                          >Delete</button>
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
