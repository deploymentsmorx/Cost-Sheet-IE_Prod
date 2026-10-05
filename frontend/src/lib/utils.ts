import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function fmt(value: string | null | undefined): string {
  if (value == null) return ""
  const n = parseFloat(value)
  return isNaN(n) ? "" : n.toFixed(2)
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
  })
}

/** Compares dotted BOM level numbers ("1", "1.1", "1.10", "2") so sorting yields correct depth-first tree order. */
export function compareLevelNo(a: string, b: string): number {
  const pa = a.split(".").map(Number)
  const pb = b.split(".").map(Number)
  const len = Math.max(pa.length, pb.length)
  for (let i = 0; i < len; i++) {
    const x = pa[i] ?? -1
    const y = pb[i] ?? -1
    if (x !== y) return x - y
  }
  return 0
}

/** BOM nesting depth from a dotted level number ("1" -> 0, "1.1" -> 1, "1.1.1" -> 2). */
export function levelDepth(levelNo: string | null | undefined): number {
  if (!levelNo) return 0
  return levelNo.split(".").length - 1
}
