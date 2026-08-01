import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { normsApi } from "../../api/norms"
import { partsApi } from "../../api/parts"
import type { CostingLine, RmLineResult } from "../../types/parts"
import { Button } from "../ui/button"

const BANDS = ["<10mm", "12mm", ">12-19mm", "20mm", ">20-40mm", ">40-63mm", "80mm"]

function n(v: string | number | undefined | null, dp = 2) {
  if (v == null || v === "") return "—"
  return Number(v).toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

interface PreviewRowProps { label: string; value: string | number | undefined | null; bold?: boolean }
function PreviewRow({ label, value, bold }: PreviewRowProps) {
  return (
    <tr className={bold ? "font-semibold" : ""}>
      <td className="py-0.5 pr-3 text-xs text-slate-500">{label}</td>
      <td className="py-0.5 text-right text-xs font-mono tabular-nums text-slate-800">{n(value?.toString())}</td>
    </tr>
  )
}

interface Props {
  sheetId: number
  clientId: number | null
  editing: CostingLine | null
  onSaved: () => void
  onCancel: () => void
}

interface FormState {
  description: string
  spec: string
  grade_id: string
  thickness_band: string
  thickness_mm: string
  qty: string
  part_weight: string
  efficiency_pct: string
}

function blankForm(): FormState {
  return {
    description: "", spec: "", grade_id: "", thickness_band: "",
    thickness_mm: "", qty: "1", part_weight: "0", efficiency_pct: "90",
  }
}

function lineToForm(l: CostingLine): FormState {
  return {
    description: l.description ?? "",
    spec: l.spec ?? "",
    grade_id: l.grade_id?.toString() ?? "",
    thickness_band: l.thickness_band ?? "",
    thickness_mm: l.thickness_mm ?? "",
    qty: l.qty,
    part_weight: l.part_weight,
    efficiency_pct: l.efficiency_pct,
  }
}

const inputCls = "border border-slate-200 rounded-lg px-3 py-2 text-sm w-full bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
const labelCls = "text-xs font-semibold text-slate-500 mb-1.5 block uppercase tracking-wide"

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-[11px] font-bold uppercase tracking-widest text-slate-400">{children}</span>
      <div className="flex-1 h-px bg-slate-100" />
    </div>
  )
}

export function LineEditorPanel({ sheetId, clientId, editing, onSaved, onCancel }: Props) {
  const [form, setForm] = useState<FormState>(editing ? lineToForm(editing) : blankForm())
  const [preview, setPreview] = useState<RmLineResult | null>(editing?.rm_result ?? null)
  const [saving, setSaving] = useState(false)

  const { data: lookup } = useQuery({
    queryKey: ["norms-lookup", clientId],
    queryFn: () => normsApi.lookup(clientId!),
    staleTime: 60_000,
    enabled: clientId != null,
  })

  const set = (key: keyof FormState, value: string) => {
    const next = { ...form, [key]: value }
    setForm(next)
    // Trigger live RM preview when grade + band are set
    if (next.grade_id && next.thickness_band) {
      triggerPreview(next)
    } else {
      setPreview(null)
    }
  }

  const previewTimer = { current: null as ReturnType<typeof setTimeout> | null }

  function triggerPreview(f: FormState) {
    if (previewTimer.current) clearTimeout(previewTimer.current)
    previewTimer.current = setTimeout(async () => {
      try {
        const res = await fetch("/api/v1/calculate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            grade_id: Number(f.grade_id),
            thickness_band: f.thickness_band,
            part_weight: f.part_weight || "0",
            qty: f.qty || "1",
            efficiency_pct: f.efficiency_pct || "100",
            thickness_mm: f.thickness_mm || "0",
            client_id: clientId,
          }),
        })
        if (res.ok) setPreview(await res.json())
      } catch { /* ignore */ }
    }, 350)
  }

  async function save() {
    setSaving(true)
    try {
      const body = {
        description: form.description || null,
        spec: form.spec || null,
        grade_id: form.grade_id ? Number(form.grade_id) : null,
        thickness_band: form.thickness_band || null,
        thickness_mm: form.thickness_mm ? Number(form.thickness_mm) : null,
        qty: form.qty,
        part_weight: form.part_weight,
        efficiency_pct: form.efficiency_pct,
      }
      if (editing) await partsApi.updateLine(sheetId, editing.id, body)
      else await partsApi.addLine(sheetId, body)
      onSaved()
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/60">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">{editing ? `Edit Line ${editing.sl_no}` : "New RM Line"}</h3>
          <p className="text-xs text-slate-400 mt-0.5">Material selection and weights. Process ops are added inline in the table below.</p>
        </div>
        <button onClick={onCancel} className="text-slate-400 hover:text-slate-700 transition-colors text-lg leading-none w-7 h-7 flex items-center justify-center rounded-md hover:bg-slate-100">✕</button>
      </div>

      <div className="flex flex-col lg:flex-row divide-y lg:divide-y-0 lg:divide-x divide-slate-100">
        {/* Left: inputs */}
        <div className="flex-1 p-6 space-y-5 min-w-0">
          <div>
            <SectionLabel>Basic Info</SectionLabel>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Description</label>
                <input value={form.description} onChange={e => set("description", e.target.value)} className={inputCls} placeholder="e.g. Side Plate" />
              </div>
              <div>
                <label className={labelCls}>Spec / Material Spec</label>
                <input value={form.spec} onChange={e => set("spec", e.target.value)} className={inputCls} placeholder="e.g. IS 2062 E250" />
              </div>
            </div>
          </div>

          <div>
            <SectionLabel>Material Selection</SectionLabel>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className={labelCls}>Grade *</label>
                <select value={form.grade_id} onChange={e => set("grade_id", e.target.value)} className={inputCls}>
                  <option value="">— select —</option>
                  {lookup?.material_grades.map(g => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelCls}>Thickness Band *</label>
                <select value={form.thickness_band} onChange={e => set("thickness_band", e.target.value)} className={inputCls}>
                  <option value="">— select —</option>
                  {BANDS.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls}>Thickness (mm)</label>
                <input type="number" min="0" step="0.1" value={form.thickness_mm} onChange={e => set("thickness_mm", e.target.value)} className={inputCls} placeholder="actual mm" />
              </div>
            </div>
          </div>

          <div>
            <SectionLabel>Quantities & Weights</SectionLabel>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className={labelCls}>Quantity</label>
                <input type="number" min="1" step="1" value={form.qty} onChange={e => set("qty", e.target.value)} className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Part Weight (kg/pc)</label>
                <input type="number" min="0" step="0.001" value={form.part_weight} onChange={e => set("part_weight", e.target.value)} className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Efficiency %</label>
                <input type="number" min="1" max="100" step="0.1" value={form.efficiency_pct} onChange={e => set("efficiency_pct", e.target.value)} className={inputCls} />
              </div>
            </div>
          </div>

          <div className="flex gap-2 justify-end pt-3 border-t border-slate-100">
            <Button variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
            <Button size="sm" onClick={save} disabled={saving}>
              {saving ? "Saving…" : editing ? "Update Line" : "Add Line"}
            </Button>
          </div>
        </div>

        {/* Right: RM preview */}
        <div className="lg:w-64 shrink-0 bg-slate-50/60">
          <div className="px-5 py-4 border-b border-slate-100">
            <h4 className="text-xs font-bold uppercase tracking-widest text-slate-400">RM Chain Preview</h4>
          </div>
          <div className="px-5 py-4">
            {!preview ? (
              <p className="text-xs text-slate-400 italic">Select grade and band to preview RM cost.</p>
            ) : (
              <table className="w-full">
                <tbody>
                  <tr><td colSpan={2} className="pb-1 text-[10px] font-bold uppercase tracking-widest text-slate-400">Weights (kg)</td></tr>
                  <PreviewRow label="Part Wt / pc"    value={preview.part_weight} />
                  <PreviewRow label="Blank Wt / pc"   value={preview.blank_weight} />
                  <PreviewRow label="Total Part Wt"   value={preview.total_part_weight} bold />
                  <PreviewRow label="Total Blank Wt"  value={preview.total_blank_weight} bold />

                  <tr><td colSpan={2} className="pt-4 pb-1 text-[10px] font-bold uppercase tracking-widest text-slate-400">RM Chain (₹)</td></tr>
                  <PreviewRow label="Blank Rate"       value={preview.blank_rate} />
                  <PreviewRow label="Blank Cost"       value={preview.blank_cost} />
                  <PreviewRow label={`Proc. Loss (${n(preview.process_loss_pct, 0)}%)`} value={preview.process_loss_weight} />
                  <PreviewRow label="Scrap Credit"     value={preview.scrap_cost} />
                  <PreviewRow label="RM Cost"          value={preview.rm_cost} bold />
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
