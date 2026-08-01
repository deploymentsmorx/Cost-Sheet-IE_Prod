import { useEffect, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { normsApi } from "../../api/norms"
import type { MaterialGrade, NormLibraryDetail, RmPriceBand } from "../../types/norms"
import { Button } from "../ui/button"
import { cn, fmt, fmtDate } from "../../lib/utils"

const THICKNESS_ORDER = ["<10mm", "12mm", ">12-19mm", "20mm", ">20-40mm", ">40-63mm", "80mm"]

const UNITS = ["Rs/Kg", "Rs/Hr", "Rs/mm/meter", "Rs/slant/meter", "Rs/Nos", "Rs/Sqm", "%"]

interface Props {
  detail: NormLibraryDetail
  readOnly: boolean
}

type PriceMap = Record<number, Record<string, string>>
type DateMap  = Record<number, Record<string, string>>

function buildMaps(bands: RmPriceBand[]) {
  const prices: PriceMap = {}
  const dates: DateMap  = {}
  for (const b of bands) {
    if (!prices[b.grade_id]) { prices[b.grade_id] = {}; dates[b.grade_id] = {} }
    prices[b.grade_id][b.thickness_band] = b.price_per_kg
    dates[b.grade_id][b.thickness_band]  = b.updated_at
  }
  return { prices, dates }
}

interface AddGradeFormState {
  name: string
  isDerived: boolean
  baseGradeId: string
  premiumAmount: string
  initialPrice: string
}

const emptyAdd: AddGradeFormState = { name: "", isDerived: false, baseGradeId: "", premiumAmount: "", initialPrice: "0" }

export function RmPriceMatrix({ detail, readOnly }: Props) {
  const qc = useQueryClient()
  const { library: version, material_grades, rm_price_bands, scrap_rate } = detail

  const baseGrades   = material_grades.filter(g => g.base_grade_id == null)
  const derivedGrades = material_grades.filter(g => g.base_grade_id != null)
  const e250br = material_grades.find(g => g.name === "IS2062 E250BR")
  const e350c  = derivedGrades.find(g => g.base_grade_id === e250br?.id)

  const [{ prices, dates }, setMaps] = useState(() => buildMaps(rm_price_bands))
  const [premium, setPremium] = useState(fmt(e350c?.premium_amount ?? "5"))
  const [premiumDate, setPremiumDate] = useState(e350c?.updated_at ?? "")
  const [scrap, setScrap]     = useState(fmt(scrap_rate?.rate_per_kg ?? "0"))
  const [scrapDate, setScrapDate] = useState(scrap_rate?.updated_at ?? "")
  const [dirty, setDirty]     = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [addForm, setAddForm] = useState<AddGradeFormState>(emptyAdd)

  useEffect(() => {
    setMaps(buildMaps(rm_price_bands))
    setPremium(fmt(e350c?.premium_amount ?? "5"))
    setPremiumDate(e350c?.updated_at ?? "")
    setScrap(fmt(scrap_rate?.rate_per_kg ?? "0"))
    setScrapDate(scrap_rate?.updated_at ?? "")
    setDirty(false)
  }, [detail])

  const saveMutation = useMutation({
    mutationFn: () => {
      const priceUpdates = rm_price_bands.map(b => ({
        grade_id: b.grade_id,
        thickness_band: b.thickness_band,
        price_per_kg: prices[b.grade_id]?.[b.thickness_band] ?? b.price_per_kg,
      }))
      const gradePremiumUpdates = e350c ? [{ grade_id: e350c.id, premium_amount: premium }] : []
      return normsApi.updateRmPrices(version.id, {
        scrap_rate: scrap,
        price_updates: priceUpdates,
        grade_premium_updates: gradePremiumUpdates,
      })
    },
    onSuccess: data => { qc.setQueryData(["library", version.id], data); setDirty(false); toast.success("RM prices saved") },
    onError: (e: Error) => toast.error(e.message),
  })

  const addGradeMutation = useMutation({
    mutationFn: () => normsApi.addGrade(version.id, {
      name: addForm.name.trim(),
      base_grade_id: addForm.isDerived ? Number(addForm.baseGradeId) : undefined,
      premium_amount: addForm.isDerived ? addForm.premiumAmount : undefined,
      initial_price:  !addForm.isDerived ? addForm.initialPrice : undefined,
    }),
    onSuccess: data => {
      qc.setQueryData(["library", version.id], data)
      setShowAdd(false)
      setAddForm(emptyAdd)
      toast.success(`Grade "${addForm.name}" added`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  function setPrice(gradeId: number, band: string, val: string) {
    setMaps(prev => ({
      prices: { ...prev.prices, [gradeId]: { ...prev.prices[gradeId], [band]: val } },
      dates:  prev.dates,
    }))
    setDirty(true)
  }

  function e350cPrice(band: string): string {
    if (!e250br) return ""
    const base = parseFloat(prices[e250br.id]?.[band] ?? "0")
    const p    = parseFloat(premium)
    if (isNaN(base) || isNaN(p)) return ""
    return (base + p).toFixed(2)
  }

  const displayGrades: Array<MaterialGrade & { isDerived: boolean }> = [
    ...baseGrades.map(g => ({ ...g, isDerived: false })),
    ...derivedGrades.map(g => ({ ...g, isDerived: true })),
  ]

  return (
    <div className="space-y-4">
      {/* Premium + scrap */}
      <div className="flex flex-wrap gap-6 items-start">
        {e350c && (
          <div>
            <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
              E350C Premium over E250BR (Rs/Kg)
            </label>
            <input type="number" step="0.01" min="0" value={premium} disabled={readOnly}
              onChange={e => { setPremium(e.target.value); setDirty(true) }}
              className="w-28 border rounded px-2 py-1.5 text-sm disabled:bg-muted" />
            <div className="text-[11px] text-muted-foreground mt-0.5">Last amended: {fmtDate(premiumDate)}</div>
          </div>
        )}
        <div>
          <label className="block text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Scrap Rate (Rs/Kg)
          </label>
          <input type="number" step="0.01" min="0" value={scrap} disabled={readOnly}
            onChange={e => { setScrap(e.target.value); setDirty(true) }}
            className="w-28 border rounded px-2 py-1.5 text-sm disabled:bg-muted" />
          <div className="text-[11px] text-muted-foreground mt-0.5">Last amended: {fmtDate(scrapDate)}</div>
        </div>
      </div>

      {/* Price matrix */}
      <div className="overflow-x-auto rounded border">
        <table className="text-sm w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="border-b px-3 py-2 text-left font-semibold whitespace-nowrap w-32">Thickness Band</th>
              {displayGrades.map(g => (
                <th key={g.id} className="border-b border-l px-3 py-2 text-right font-semibold whitespace-nowrap min-w-[130px]">
                  {g.name}
                  {g.isDerived && (
                    <div className="text-xs font-normal text-muted-foreground">= E250BR + {premium}</div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {THICKNESS_ORDER.map((band, i) => (
              <tr key={band} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                <td className="border-b px-3 py-1 font-medium whitespace-nowrap">{band}</td>
                {displayGrades.map(g => {
                  if (g.isDerived) {
                    return (
                      <td key={g.id} className="border-b border-l px-3 py-1 text-right text-muted-foreground bg-muted/20 text-sm">
                        {e350cPrice(band)}
                      </td>
                    )
                  }
                  const amendedDate = fmtDate(dates[g.id]?.[band])
                  return (
                    <td key={g.id} className="border-b border-l px-1 py-0.5 group relative">
                      <input
                        type="number" step="0.01" min="0"
                        value={prices[g.id]?.[band] ?? ""}
                        disabled={readOnly}
                        onChange={e => setPrice(g.id, band, e.target.value)}
                        className="w-full text-right px-2 py-1 rounded text-sm border-0 bg-transparent focus:bg-white focus:border focus:outline-none focus:ring-1 focus:ring-ring disabled:text-muted-foreground"
                      />
                      {/* Amended date tooltip */}
                      <div className="absolute bottom-full right-0 mb-1 z-10 hidden group-hover:block">
                        <div className="bg-gray-800 text-white text-[11px] px-2 py-1 rounded whitespace-nowrap shadow-lg">
                          Last amended: {amendedDate}
                        </div>
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add grade form */}
      {!readOnly && showAdd && (
        <div className="border rounded-lg p-4 bg-muted/30 space-y-3">
          <p className="text-sm font-medium">Add New Grade</p>
          <div className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Grade Name</label>
              <input value={addForm.name} onChange={e => setAddForm(p => ({ ...p, name: e.target.value }))}
                placeholder="e.g. IS2062 E450D" className="border rounded px-2 py-1.5 text-sm w-44" />
            </div>
            <label className="flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" checked={addForm.isDerived}
                onChange={e => setAddForm(p => ({ ...p, isDerived: e.target.checked }))} />
              Derived (Base + Premium)
            </label>
            {addForm.isDerived ? (
              <>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Base Grade</label>
                  <select value={addForm.baseGradeId}
                    onChange={e => setAddForm(p => ({ ...p, baseGradeId: e.target.value }))}
                    className="border rounded px-2 py-1.5 text-sm">
                    <option value="">— select —</option>
                    {baseGrades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Premium (Rs/Kg)</label>
                  <input type="number" step="0.01" min="0" value={addForm.premiumAmount}
                    onChange={e => setAddForm(p => ({ ...p, premiumAmount: e.target.value }))}
                    className="border rounded px-2 py-1.5 text-sm w-24" />
                </div>
              </>
            ) : (
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Initial Price (Rs/Kg, all bands)</label>
                <input type="number" step="0.01" min="0" value={addForm.initialPrice}
                  onChange={e => setAddForm(p => ({ ...p, initialPrice: e.target.value }))}
                  className="border rounded px-2 py-1.5 text-sm w-28" />
              </div>
            )}
            <Button size="sm" onClick={() => addGradeMutation.mutate()} disabled={!addForm.name || addGradeMutation.isPending}>
              {addGradeMutation.isPending ? "Adding…" : "Add Grade"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { setShowAdd(false); setAddForm(emptyAdd) }}>Cancel</Button>
          </div>
        </div>
      )}

      {/* Action row */}
      {!readOnly && (
        <div className="flex justify-between">
          <Button variant="outline" size="sm" onClick={() => setShowAdd(v => !v)}>
            {showAdd ? "Cancel Add Grade" : "+ Add Grade"}
          </Button>
          <Button onClick={() => saveMutation.mutate()} disabled={!dirty || saveMutation.isPending} size="sm">
            {saveMutation.isPending ? "Saving…" : "Save RM Prices"}
          </Button>
        </div>
      )}
    </div>
  )
}
