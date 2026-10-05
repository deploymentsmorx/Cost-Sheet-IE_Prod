import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { normsApi } from "../../api/norms"
import type { NormLibraryDetail } from "../../types/norms"
import { fmtDate } from "../../lib/utils"

const BANDS = ["<10mm", "12mm", ">12-19mm", "20mm", ">20-40mm", ">40-63mm", "80mm"]

interface Props {
  detail: NormLibraryDetail
  clientId: number
}

export function RmPriceTrend({ detail, clientId }: Props) {
  const [gradeId, setGradeId] = useState<number | "">(detail.material_grades[0]?.id ?? "")
  const [band, setBand] = useState("20mm")

  const { data: points, isLoading } = useQuery({
    queryKey: ["rm-price-trend", clientId, gradeId, band],
    queryFn: () => normsApi.rmPriceTrend(clientId, gradeId as number, band),
    enabled: gradeId !== "",
  })

  const prices = (points ?? []).map(p => Number(p.price_per_kg))
  const maxPrice = prices.length ? Math.max(...prices) : 0
  const minPrice = prices.length ? Math.min(...prices) : 0

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        How a grade's RM price has moved across every norm library version — each published/draft/historical version is one data point.
      </p>
      <div className="flex items-end gap-3">
        <div>
          <label className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1 block">Grade</label>
          <select
            value={gradeId}
            onChange={e => setGradeId(e.target.value === "" ? "" : Number(e.target.value))}
            className="border rounded px-2.5 py-1.5 text-sm min-w-[180px]"
          >
            {detail.material_grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
        </div>
        <div>
          <label className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1 block">Thickness Band</label>
          <select value={band} onChange={e => setBand(e.target.value)} className="border rounded px-2.5 py-1.5 text-sm">
            {BANDS.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
        </div>
      </div>

      {isLoading ? (
        <p className="text-xs text-slate-400 italic">Loading trend…</p>
      ) : !points || points.length === 0 ? (
        <p className="text-xs text-slate-400 italic">No RM price recorded for this grade + band in any library version yet.</p>
      ) : (
        <div className="overflow-x-auto rounded border">
          <table className="text-sm w-full border-collapse">
            <thead>
              <tr className="bg-muted">
                <th className="border-b px-3 py-2 text-left font-semibold">Library Version</th>
                <th className="border-b border-l px-3 py-2 text-left font-semibold w-32">Effective Date</th>
                <th className="border-b border-l px-3 py-2 text-left font-semibold w-28">Status</th>
                <th className="border-b border-l px-3 py-2 text-right font-semibold w-24">Rs/Kg</th>
                <th className="border-b border-l px-3 py-2 font-semibold w-48">Trend</th>
              </tr>
            </thead>
            <tbody>
              {points.map((p, i) => {
                const price = Number(p.price_per_kg)
                const prev = i > 0 ? Number(points[i - 1].price_per_kg) : null
                const delta = prev != null && prev !== 0 ? ((price - prev) / prev) * 100 : null
                const barPct = maxPrice > minPrice ? ((price - minPrice) / (maxPrice - minPrice)) * 100 : 100
                return (
                  <tr key={p.norm_library_id} className={i % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                    <td className="border-b px-3 py-1.5">{p.label}</td>
                    <td className="border-b border-l px-3 py-1.5 text-xs text-muted-foreground">{fmtDate(p.effective_date)}</td>
                    <td className="border-b border-l px-3 py-1.5">
                      <span className={
                        p.is_current ? "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200" :
                        p.is_draft ? "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200" :
                        "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 border border-slate-200"
                      }>
                        {p.is_current ? "Current" : p.is_draft ? "Draft" : "Historical"}
                      </span>
                    </td>
                    <td className="border-b border-l px-3 py-1.5 text-right font-mono font-semibold">
                      {price.toFixed(2)}
                      {delta != null && (
                        <span className={delta > 0 ? "text-red-600 text-[10px] ml-1" : delta < 0 ? "text-emerald-600 text-[10px] ml-1" : "text-slate-400 text-[10px] ml-1"}>
                          ({delta > 0 ? "+" : ""}{delta.toFixed(1)}%)
                        </span>
                      )}
                    </td>
                    <td className="border-b border-l px-3 py-1.5">
                      <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-sky-400 rounded-full" style={{ width: `${Math.max(barPct, 4)}%` }} />
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
