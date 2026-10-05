import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Pencil, Check, X } from "lucide-react"
import { normsApi } from "../api/norms"
import { clientsApi } from "../api/clients"
import { RmPriceMatrix } from "../components/norms/RmPriceMatrix"
import { ProcessRatesTable } from "../components/norms/ProcessRatesTable"
import { OverheadParams } from "../components/norms/OverheadParams"
import { SteelPriceBuildUp } from "../components/norms/SteelPriceBuildUp"
import { GradeEquivalenceTable } from "../components/norms/GradeEquivalenceTable"
import { SectionCatalogTable } from "../components/norms/SectionCatalogTable"
import { BoughtOutCatalog } from "../components/norms/BoughtOutCatalog"
import { RmPriceTrend } from "../components/norms/RmPriceTrend"
import { Button } from "../components/ui/button"
import { cn } from "../lib/utils"

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60">
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
      </div>
      <div className="p-6">
        {children}
      </div>
    </section>
  )
}

const inputCls = "border border-slate-200 rounded-lg px-3 py-2 text-sm w-full bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"

export function NormsPage() {
  const qc = useQueryClient()

  // Client filter
  const [clientFilter, setClientFilter] = useState<number | "">("")

  const { data: clients = [] } = useQuery({
    queryKey: ["clients"],
    queryFn: () => clientsApi.list(),
  })

  const { data: versions = [], isLoading: versionsLoading } = useQuery({
    queryKey: ["libraries", clientFilter],
    queryFn: () => normsApi.listLibraries(clientFilter !== "" ? clientFilter : undefined),
  })

  const currentVersion = versions.find((v) => v.is_current)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const activeId = selectedId ?? currentVersion?.id ?? null

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["library", activeId],
    queryFn: () => normsApi.getLibrary(activeId!),
    enabled: activeId != null,
  })

  const selectedVersion = versions.find((v) => v.id === activeId)
  const isCurrentSelected = selectedVersion?.is_current ?? false
  const readOnly = !isCurrentSelected && !(selectedVersion?.is_draft)
  const canRename = isCurrentSelected || (selectedVersion?.is_draft ?? false)

  // Rename state
  const [renaming, setRenaming] = useState(false)
  const [renameLabel, setRenameLabel] = useState("")

  // Create new library form
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({ client_id: "" as number | "", label: "", seed_defaults: true })

  function startRename() {
    setRenameLabel(selectedVersion?.label ?? "")
    setRenaming(true)
  }
  function cancelRename() {
    setRenaming(false)
    setRenameLabel("")
  }

  const createLibraryMutation = useMutation({
    mutationFn: () => normsApi.createLibrary({
      client_id: createForm.client_id as number,
      label: createForm.label.trim(),
      seed_defaults: createForm.seed_defaults,
    }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["libraries"] })
      qc.setQueryData(["library", data.library.id], data)
      setSelectedId(data.library.id)
      setClientFilter(data.library.client_id)
      setShowCreateForm(false)
      setCreateForm({ client_id: "", label: "", seed_defaults: true })
      toast.success(`Created library: "${data.library.label}"`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const deleteLibraryMutation = useMutation({
    mutationFn: () => normsApi.deleteLibrary(activeId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["libraries"] })
      setSelectedId(null)
      toast.success("Draft library deleted")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const duplicateMutation = useMutation({
    mutationFn: () => normsApi.duplicate(activeId!),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["libraries"] })
      qc.setQueryData(["library", data.library.id], data)
      setSelectedId(data.library.id)
      toast.success(`Created draft: "${data.library.label}"`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const publishMutation = useMutation({
    mutationFn: () => normsApi.publish(activeId!),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["libraries"] })
      qc.setQueryData(["library", data.library.id], data)
      toast.success(`Published "${data.library.label}" — it is now the current version`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const renameMutation = useMutation({
    mutationFn: () => normsApi.rename(activeId!, renameLabel.trim()),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["libraries"] })
      qc.setQueryData(["library", data.library.id], data)
      setRenaming(false)
      toast.success(`Renamed to "${data.library.label}"`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  if (versionsLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading versions…</div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">

      {/* Page header + toolbar */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Norms Library</h1>
          <p className="text-sm text-slate-500 mt-1">Manage RM prices, process rates, and overhead parameters</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">

          {/* Client filter */}
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide shrink-0">Client</span>
            <select
              value={clientFilter}
              onChange={e => {
                setClientFilter(e.target.value === "" ? "" : Number(e.target.value))
                setSelectedId(null)
              }}
              className="text-sm bg-transparent focus:outline-none text-slate-700 font-medium min-w-[160px]"
            >
              <option value="">All clients</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          {/* Version picker / rename */}
          {versions.length > 0 && (
            <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide shrink-0">Version</span>

              {renaming ? (
                <div className="flex items-center gap-1">
                  <input
                    autoFocus
                    value={renameLabel}
                    onChange={e => setRenameLabel(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === "Enter" && renameLabel.trim()) renameMutation.mutate()
                      if (e.key === "Escape") cancelRename()
                    }}
                    className="text-sm text-slate-700 font-medium focus:outline-none border-b border-primary w-44 bg-transparent pb-0.5"
                  />
                  <button
                    onClick={() => renameMutation.mutate()}
                    disabled={!renameLabel.trim() || renameMutation.isPending}
                    className="text-emerald-600 hover:text-emerald-700 disabled:opacity-40 p-0.5 rounded transition-colors"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button onClick={cancelRename} className="text-slate-400 hover:text-slate-600 p-0.5 rounded transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-1.5">
                  <select
                    value={activeId ?? ""}
                    onChange={(e) => { setSelectedId(Number(e.target.value)); setRenaming(false) }}
                    className="text-sm bg-transparent focus:outline-none text-slate-700 font-medium min-w-[180px]"
                  >
                    {versions.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.label}
                        {v.is_current ? " (current)" : ""}
                        {v.is_draft ? " [draft]" : ""}
                      </option>
                    ))}
                  </select>
                  {canRename && (
                    <button
                      onClick={startRename}
                      className="text-slate-300 hover:text-slate-600 p-0.5 rounded transition-colors"
                      title="Rename this version"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Status badge */}
          {selectedVersion && (
            <span className={cn(
              "text-xs font-semibold px-2.5 py-1 rounded-full border",
              isCurrentSelected
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : selectedVersion.is_draft
                ? "bg-amber-50 text-amber-700 border-amber-200"
                : "bg-slate-100 text-slate-500 border-slate-200"
            )}>
              {isCurrentSelected ? "● Current" : selectedVersion.is_draft ? "● Draft" : "Historical"}
            </span>
          )}

          <Button
            variant="outline" size="sm"
            onClick={() => { setShowCreateForm(v => !v); setRenaming(false) }}
          >
            + New Library
          </Button>

          {versions.length > 0 && (
            <>
              <Button
                variant="outline" size="sm"
                onClick={() => duplicateMutation.mutate()}
                disabled={!activeId || duplicateMutation.isPending}
              >
                {duplicateMutation.isPending ? "Creating…" : "Duplicate Version"}
              </Button>
              <Button
                size="sm"
                onClick={() => publishMutation.mutate()}
                disabled={!activeId || isCurrentSelected || !selectedVersion?.is_draft || publishMutation.isPending}
              >
                {publishMutation.isPending ? "Publishing…" : "Publish Version"}
              </Button>
              {selectedVersion?.is_draft && (
                <Button
                  variant="outline" size="sm"
                  className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                  onClick={() => {
                    if (confirm(`Delete draft "${selectedVersion.label}"? This cannot be undone.`))
                      deleteLibraryMutation.mutate()
                  }}
                  disabled={deleteLibraryMutation.isPending}
                >
                  {deleteLibraryMutation.isPending ? "Deleting…" : "Delete Draft"}
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Create New Library form */}
      {showCreateForm && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60">
            <h2 className="text-sm font-semibold text-slate-900">Create New Norm Library</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-4 max-w-xl">
              <div>
                <label className="text-xs font-semibold text-slate-500 mb-1.5 block uppercase tracking-wide">Client *</label>
                <select
                  value={createForm.client_id}
                  onChange={e => setCreateForm(f => ({ ...f, client_id: e.target.value === "" ? "" : Number(e.target.value) }))}
                  className={inputCls}
                >
                  <option value="">Select a client…</option>
                  {clients.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-500 mb-1.5 block uppercase tracking-wide">Library Label *</label>
                <input
                  autoFocus
                  value={createForm.label}
                  onChange={e => setCreateForm(f => ({ ...f, label: e.target.value }))}
                  placeholder="e.g. Base Rates 2025"
                  className={inputCls}
                />
              </div>
            </div>

            <label className="flex items-start gap-3 cursor-pointer select-none mt-2 max-w-xl p-3 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={createForm.seed_defaults}
                onChange={e => setCreateForm(f => ({ ...f, seed_defaults: e.target.checked }))}
                className="mt-0.5 h-4 w-4 rounded border-slate-300 accent-primary"
              />
              <div>
                <p className="text-sm font-semibold text-slate-800">Pre-seed with TLD default rates</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Fills in RM prices (Apr 2026), 29 process rates, and overhead parameters from TLD source data.
                  You can edit any value after creation.
                </p>
              </div>
            </label>

            <div className="flex gap-2 mt-4 pt-4 border-t border-slate-100 justify-end">
              <Button variant="ghost" size="sm" onClick={() => { setShowCreateForm(false); setCreateForm({ client_id: "", label: "", seed_defaults: true }) }}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => createLibraryMutation.mutate()}
                disabled={createForm.client_id === "" || !createForm.label.trim() || createLibraryMutation.isPending}
              >
                {createLibraryMutation.isPending ? "Creating…" : "Create Library"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Read-only banner */}
      {readOnly && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800 flex items-center gap-2">
          <span className="text-amber-500 text-base">⚠</span>
          Viewing historical version — read only. Use "Duplicate Version" to make changes.
        </div>
      )}

      {/* Empty state */}
      {versions.length === 0 && !showCreateForm && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-20 text-center">
          <h3 className="text-sm font-semibold text-slate-900 mb-1">No norm libraries yet</h3>
          <p className="text-sm text-slate-500 mb-5">
            {clientFilter !== "" ? "No libraries for this client." : "Create a library to set up RM prices, process rates, and overhead parameters."}
          </p>
          <Button size="sm" onClick={() => setShowCreateForm(true)}>+ New Library</Button>
        </div>
      )}

      {/* Content sections */}
      {activeId && (
        detailLoading || !detail ? (
          <div className="flex items-center justify-center h-40 text-slate-400 text-sm">Loading…</div>
        ) : (
          <div className="space-y-6">
            <Section title="1 — Raw Material Price Matrix (Rs/Kg)">
              <RmPriceMatrix detail={detail} readOnly={readOnly} />
            </Section>

            <Section title="2 — Process Rates">
              <ProcessRatesTable detail={detail} readOnly={readOnly} />
            </Section>

            <Section title="3 — Overhead & Profit Parameters">
              <OverheadParams detail={detail} readOnly={readOnly} />
            </Section>

            <Section title="4 — Steel Price Build-Up">
              <SteelPriceBuildUp detail={detail} readOnly={readOnly} />
            </Section>

            <Section title="5 — Grade Equivalence Mapping">
              <GradeEquivalenceTable detail={detail} readOnly={readOnly} />
            </Section>

            <Section title="6 — Section / Bar / Tube Catalogue">
              <SectionCatalogTable detail={detail} readOnly={readOnly} />
            </Section>

            <Section title="7 — Bought-Out Item Master">
              <BoughtOutCatalog detail={detail} readOnly={readOnly} />
            </Section>

            <Section title="8 — RM Price Trend">
              <RmPriceTrend detail={detail} clientId={detail.library.client_id} />
            </Section>
          </div>
        )
      )}
    </div>
  )
}
