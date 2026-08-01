import { useNavigate, useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ChevronRight, BarChart3 } from "lucide-react"
import { partsApi } from "../api/parts"
import { Button } from "../components/ui/button"

function fmt(v: string | number | null | undefined, dp = 2) {
  if (v == null || v === "") return "—"
  return Number(v).toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

function fmtDate(s: string | null | undefined) {
  if (!s) return "—"
  return new Date(s).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
}

const sub = "px-3 py-3 text-right text-xs tabular-nums"

export function ProjectSummaryPage() {
  const { workbookId } = useParams<{ workbookId: string }>()
  const wid = Number(workbookId)
  const navigate = useNavigate()

  const { data: summary, isLoading } = useQuery({
    queryKey: ["summary", wid],
    queryFn: () => partsApi.getSummary(wid),
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-slate-400 text-sm">Loading…</div>
  )
  if (!summary) return null

  return (
    <div className="max-w-full px-6 py-8 space-y-6">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm">
        <button onClick={() => navigate("/workbooks")} className="text-slate-500 hover:text-slate-900 transition-colors font-medium">
          Costing Workbooks
        </button>
        <ChevronRight className="w-4 h-4 text-slate-400" />
        <span className="text-slate-900 font-semibold">{summary.name}</span>
        {summary.client_name && <span className="text-slate-400 ml-0.5">— {summary.client_name}</span>}
      </nav>

      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Summary</h1>
          <p className="text-sm text-slate-500 mt-1">All cost sheets in this workbook</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => navigate(`/workbooks/${wid}/sheets`)}>
          Manage Sheets
        </Button>
      </div>

      {summary.cost_sheets.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
            <BarChart3 className="w-7 h-7 text-slate-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 mb-1">No cost sheets yet</h3>
          <p className="text-sm text-slate-500 mb-5">Add cost sheets to this workbook to see the summary</p>
          <Button size="sm" onClick={() => navigate(`/workbooks/${wid}/sheets`)}>
            Add Cost Sheet
          </Button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
          <table className="w-full text-xs whitespace-nowrap border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500">
                <th className="px-4 py-3 font-semibold text-left text-xs uppercase tracking-wider border-r border-slate-200">#</th>
                <th className="px-4 py-3 font-semibold text-left text-xs uppercase tracking-wider border-r border-slate-200">Name</th>
                <th className="px-4 py-3 font-semibold text-left text-xs uppercase tracking-wider border-r border-slate-200">Part No.</th>
                <th className="px-4 py-3 font-semibold text-left text-xs uppercase tracking-wider border-r border-slate-200">Version</th>
                <th className="px-4 py-3 font-semibold text-right text-xs uppercase tracking-wider border-r border-slate-200">Weight (kg)</th>
                <th className="px-4 py-3 font-semibold text-right text-xs uppercase tracking-wider border-r border-slate-200">RM Cost</th>
                <th className="px-4 py-3 font-semibold text-right text-xs uppercase tracking-wider border-r border-slate-200">Unit Price</th>
                <th className="px-4 py-3 font-semibold text-right text-xs uppercase tracking-wider border-r border-slate-200">Disc %</th>
                <th className="px-4 py-3 font-semibold text-center text-xs uppercase tracking-wider border-r border-slate-200">Saved On</th>
                <th className="px-4 py-3 font-semibold text-center text-xs uppercase tracking-wider">Lines</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {summary.cost_sheets.map((s, i) => {
                const hasSaved = s.saved_count > 0
                return (
                  <tr key={s.sheet_id} className="hover:bg-slate-50/60 transition-colors align-middle">
                    <td className="px-4 py-3 text-slate-400 font-mono text-xs border-r border-slate-100">{i + 1}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 border-r border-slate-100 max-w-[200px] truncate">
                      <button
                        onClick={() => navigate(`/sheets/${s.sheet_id}`)}
                        className="hover:text-primary hover:underline transition-colors text-left"
                      >
                        {s.name}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-xs border-r border-slate-100">
                      {s.part_no ?? <span className="text-slate-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-slate-500 border-r border-slate-100">{s.supply_version}</td>
                    <td className={`${sub} border-r border-slate-100`}>
                      {hasSaved && s.total_weight ? fmt(s.total_weight, 3) + " kg" : <span className="text-slate-300">—</span>}
                    </td>
                    <td className={`${sub} border-r border-slate-100`}>
                      {hasSaved ? fmt(s.rm_cost) : <span className="text-slate-300">—</span>}
                    </td>
                    <td className={`${sub} border-r border-slate-100`}>
                      {hasSaved ? (
                        <button
                          onClick={() => navigate(`/sheets/${s.sheet_id}`)}
                          className="font-semibold text-slate-900 hover:text-primary hover:underline"
                        >
                          {fmt(s.total_price)}
                        </button>
                      ) : (
                        <button
                          onClick={() => navigate(`/sheets/${s.sheet_id}`)}
                          className="text-slate-400 hover:text-primary hover:underline"
                        >
                          {s.line_count === 0 ? "Empty" : `${s.line_count} lines — unsaved`}
                        </button>
                      )}
                    </td>
                    <td className={`${sub} border-r border-slate-100`}>
                      {hasSaved && s.discount_pct ? fmt(s.discount_pct, 1) + " %" : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-center text-slate-400 text-xs border-r border-slate-100 whitespace-nowrap">
                      {hasSaved ? fmtDate(s.saved_at) : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold">
                        {s.line_count}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-400">
        Click any sheet name or unit price to open the cost sheet editor.
      </p>
    </div>
  )
}
