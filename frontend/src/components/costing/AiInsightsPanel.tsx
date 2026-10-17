import { useState } from "react"
import { Sparkles, AlertTriangle, CheckCircle, Info, ChevronDown, ChevronUp, Loader2 } from "lucide-react"
import { Button } from "../ui/button"
import { cn } from "../../lib/utils"
import { API_BASE_URL } from "../../lib/apiBase"

// ---------------------------------------------------------------------------
// Types (mirrors backend AiInsights schema)
// ---------------------------------------------------------------------------

interface CostFlag {
  type: "warning" | "info" | "positive"
  message: string
}

interface PricingOption {
  label: string
  price: number
  margin_pct: number
  rationale: string
}

interface MaterialSuggestion {
  area: string
  suggestion: string
  estimated_saving_pct: number
}

interface MarginScenario {
  scenario: string
  margin_pct: number
}

export interface AiInsights {
  cost_analysis: string
  cost_flags: CostFlag[]
  pricing_recommendation: string
  pricing_options: PricingOption[]
  material_optimization: string
  material_suggestions: MaterialSuggestion[]
  margin_analysis: string
  margin_scenarios: MarginScenario[]
}

// ---------------------------------------------------------------------------
// Small sub-components
// ---------------------------------------------------------------------------

function FlagIcon({ type }: { type: CostFlag["type"] }) {
  if (type === "warning") return <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
  if (type === "positive") return <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
  return <Info className="w-3.5 h-3.5 text-sky-500 shrink-0 mt-0.5" />
}

function InsightCard({ title, children, accent = "border-slate-200" }: {
  title: string; children: React.ReactNode; accent?: string
}) {
  const [open, setOpen] = useState(true)
  return (
    <div className={cn("rounded-xl border bg-white shadow-sm overflow-hidden", accent)}>
      <button
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50/60 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <span className="text-xs font-bold uppercase tracking-widest text-slate-500">{title}</span>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
      </button>
      {open && <div className="px-4 pb-4 pt-1">{children}</div>}
    </div>
  )
}

function n(v: number, dp = 2) {
  return v.toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

export function AiInsightsPanel({ sheetId }: { sheetId: number }) {
  const [insights, setInsights] = useState<AiInsights | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function fetchInsights() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/api/sheets/${sheetId}/ai-insights`, { method: "POST" })
      const raw = await res.text()
      if (!res.ok) {
        const err = raw ? JSON.parse(raw) : { detail: res.statusText }
        throw new Error(err.detail ?? "AI analysis failed")
      }
      if (!raw) {
        throw new Error("Server returned an empty response — check the backend logs (e.g. a timed-out OpenAI API call).")
      }
      const data: AiInsights = JSON.parse(raw)
      setInsights(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-500" />
          <span className="text-[11px] font-bold uppercase tracking-widest text-slate-500">AI Insights</span>
        </div>
        <Button
          size="sm"
          onClick={fetchInsights}
          disabled={loading}
          className="gap-1.5 bg-violet-600 hover:bg-violet-700 text-white border-0"
        >
          {loading ? (
            <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Analysing…</>
          ) : (
            <><Sparkles className="w-3.5 h-3.5" /> {insights ? "Re-analyse" : "Get AI Insights"}</>
          )}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!insights && !loading && !error && (
        <div className="rounded-xl border border-dashed border-violet-200 bg-violet-50/30 py-10 text-center">
          <Sparkles className="w-6 h-6 text-violet-300 mx-auto mb-2" />
          <p className="text-xs text-slate-500 font-medium">Click <strong className="text-slate-700">Get AI Insights</strong> to analyse this sheet</p>
          <p className="text-[11px] text-slate-400 mt-1">Cost prediction · Pricing recommendations · Material optimisation · Margin analysis</p>
        </div>
      )}

      {/* Results */}
      {insights && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Cost Analysis */}
          <InsightCard title="Cost Analysis" accent="border-slate-200">
            <p className="text-xs text-slate-600 leading-relaxed mb-3">{insights.cost_analysis}</p>
            <div className="space-y-1.5">
              {insights.cost_flags.map((flag, i) => (
                <div key={i} className={cn(
                  "flex items-start gap-2 rounded-lg px-3 py-2 text-xs",
                  flag.type === "warning" ? "bg-amber-50 text-amber-800" :
                  flag.type === "positive" ? "bg-emerald-50 text-emerald-800" :
                  "bg-sky-50 text-sky-800"
                )}>
                  <FlagIcon type={flag.type} />
                  <span>{flag.message}</span>
                </div>
              ))}
            </div>
          </InsightCard>

          {/* Pricing Recommendation */}
          <InsightCard title="Pricing Recommendation" accent="border-emerald-200">
            <p className="text-xs text-slate-600 leading-relaxed mb-3">{insights.pricing_recommendation}</p>
            <div className="space-y-2">
              {insights.pricing_options.map((opt, i) => (
                <div key={i} className={cn(
                  "rounded-lg border px-3 py-2.5",
                  i === 1 ? "border-emerald-300 bg-emerald-50" : "border-slate-200 bg-slate-50"
                )}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={cn("text-xs font-semibold", i === 1 ? "text-emerald-700" : "text-slate-600")}>
                      {opt.label} {i === 1 && <span className="text-[10px] bg-emerald-200 text-emerald-800 px-1.5 py-0.5 rounded-full ml-1">Recommended</span>}
                    </span>
                    <span className="font-mono font-bold text-sm text-slate-800">₹{n(opt.price)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>{opt.rationale}</span>
                    <span className="font-semibold text-slate-700 ml-2 shrink-0">{n(opt.margin_pct, 1)}% margin</span>
                  </div>
                </div>
              ))}
            </div>
          </InsightCard>

          {/* Material Optimisation */}
          <InsightCard title="Material Optimisation" accent="border-amber-200">
            <p className="text-xs text-slate-600 leading-relaxed mb-3">{insights.material_optimization}</p>
            {insights.material_suggestions.length > 0 ? (
              <div className="space-y-2">
                {insights.material_suggestions.map((s, i) => (
                  <div key={i} className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-xs font-semibold text-amber-800">{s.area}</span>
                      <span className="text-[11px] font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded-full">
                        −{n(s.estimated_saving_pct, 1)}% cost
                      </span>
                    </div>
                    <p className="text-[11px] text-amber-700">{s.suggestion}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No material optimisation opportunities identified.</p>
            )}
          </InsightCard>

          {/* Margin Analysis */}
          <InsightCard title="Margin Analysis" accent="border-sky-200">
            <p className="text-xs text-slate-600 leading-relaxed mb-3">{insights.margin_analysis}</p>
            <div className="grid grid-cols-3 gap-2">
              {insights.margin_scenarios.map((s, i) => {
                const isBase = i === 0
                const isPositive = s.margin_pct > 0
                return (
                  <div key={i} className={cn(
                    "rounded-lg border text-center px-2 py-2.5",
                    isBase ? "border-sky-300 bg-sky-50" : "border-slate-200 bg-slate-50"
                  )}>
                    <p className="text-[10px] text-slate-500 mb-1 leading-tight">{s.scenario}</p>
                    <p className={cn(
                      "text-sm font-bold font-mono",
                      isPositive ? (isBase ? "text-sky-700" : "text-slate-700") : "text-red-600"
                    )}>
                      {n(s.margin_pct, 1)}%
                    </p>
                  </div>
                )
              })}
            </div>
          </InsightCard>

        </div>
      )}
    </div>
  )
}
