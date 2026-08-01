import { useState } from "react"

interface Props {
  rm: number
  bo: number
  process: number
  unitPrice: number
}

const COLORS = {
  rm:      { fill: "#6366f1", label: "RM",      bg: "bg-indigo-500" },
  bo:      { fill: "#10b981", label: "BO",       bg: "bg-emerald-500" },
  process: { fill: "#f59e0b", label: "Process",  bg: "bg-amber-400" },
}

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function arcPath(cx: number, cy: number, ro: number, ri: number, start: number, end: number) {
  if (end - start >= 360) end = start + 359.99
  const o1 = polar(cx, cy, ro, start)
  const o2 = polar(cx, cy, ro, end)
  const i1 = polar(cx, cy, ri, end)
  const i2 = polar(cx, cy, ri, start)
  const large = end - start > 180 ? 1 : 0
  return `M ${o1.x} ${o1.y} A ${ro} ${ro} 0 ${large} 1 ${o2.x} ${o2.y} L ${i1.x} ${i1.y} A ${ri} ${ri} 0 ${large} 0 ${i2.x} ${i2.y} Z`
}

function n(v: number) {
  return v.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function CostBreakdownDonut({ rm, bo, process, unitPrice }: Props) {
  const [hovered, setHovered] = useState<string | null>(null)
  const total = rm + bo + process
  if (total === 0) return null

  const slices = [
    { key: "rm",      value: rm,      ...COLORS.rm },
    { key: "bo",      value: bo,      ...COLORS.bo },
    { key: "process", value: process, ...COLORS.process },
  ].filter(s => s.value > 0)

  const cx = 80, cy = 80, ro = 72, ri = 48
  let cursor = 0
  const paths = slices.map(s => {
    const sweep = (s.value / total) * 360
    const start = cursor
    const end = cursor + sweep
    cursor = end
    return { ...s, start, end, pct: (s.value / total * 100) }
  })

  const hov = paths.find(p => p.key === hovered)

  return (
    <div className="flex items-center gap-6">
      {/* SVG donut */}
      <div className="relative shrink-0">
        <svg width="160" height="160" viewBox="0 0 160 160">
          {paths.map(p => (
            <path
              key={p.key}
              d={arcPath(cx, cy, ro, ri, p.start, p.end)}
              fill={p.fill}
              opacity={hovered && hovered !== p.key ? 0.35 : 1}
              className="cursor-pointer transition-opacity"
              onMouseEnter={() => setHovered(p.key)}
              onMouseLeave={() => setHovered(null)}
            />
          ))}
          {/* Gap rings */}
          <circle cx={cx} cy={cy} r={ro + 1} fill="none" stroke="white" strokeWidth="2" />
          <circle cx={cx} cy={cy} r={ri - 1} fill="none" stroke="white" strokeWidth="2" />
          {/* Center */}
          <text x={cx} y={cy - 8} textAnchor="middle" fontSize="10" fill="#64748b" fontFamily="inherit">Unit Price</text>
          <text x={cx} y={cy + 8} textAnchor="middle" fontSize="13" fontWeight="700" fill="#1e293b" fontFamily="inherit">
            ₹{unitPrice >= 1000 ? `${(unitPrice / 1000).toFixed(1)}k` : n(unitPrice)}
          </text>
          {hov && (
            <text x={cx} y={cy + 22} textAnchor="middle" fontSize="10" fill={hov.fill} fontFamily="inherit">
              {hov.pct.toFixed(1)}%
            </text>
          )}
        </svg>
      </div>

      {/* Legend */}
      <div className="space-y-3 min-w-[130px]">
        {paths.map(p => (
          <div
            key={p.key}
            className="cursor-default"
            onMouseEnter={() => setHovered(p.key)}
            onMouseLeave={() => setHovered(null)}
          >
            <div className="flex items-center justify-between gap-3 mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-sm shrink-0 ${p.bg}`} />
                <span className="text-xs text-slate-600 font-medium">{p.label}</span>
              </div>
              <span className="text-[11px] font-semibold text-slate-500">{p.pct.toFixed(1)}%</span>
            </div>
            <div className="text-xs font-mono text-slate-800 pl-4">₹{n(p.value)}</div>
          </div>
        ))}
        <div className="border-t border-slate-100 pt-2 mt-1">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">Unit Price</div>
          <div className="text-sm font-bold font-mono text-slate-900">₹{n(unitPrice)}</div>
        </div>
      </div>
    </div>
  )
}
