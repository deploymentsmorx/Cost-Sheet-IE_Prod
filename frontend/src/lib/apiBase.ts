// In dev (and the single-service Docker setup) this is empty, so API calls stay relative
// and go through the Vite proxy / same-origin backend. In a two-service Render deploy,
// set VITE_API_BASE_URL at build time to the backend Web Service's URL.
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ""

/** Local paths stay relative to the API; absolute S3/https URLs are used as-is. */
export function mediaUrl(path: string | null | undefined): string {
  if (!path) return ""
  if (/^https?:\/\//i.test(path)) return path
  return `${API_BASE_URL}${path}`
}
