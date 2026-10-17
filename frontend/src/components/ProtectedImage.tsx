import { useEffect, useState } from "react"
import { API_BASE_URL, mediaUrl } from "../lib/apiBase"
import { apiFetch } from "../lib/authFetch"

type Props = Omit<React.ImgHTMLAttributes<HTMLImageElement>, "src"> & { path: string | null | undefined }

export function ProtectedImage({ path, ...imageProps }: Props) {
  const [src, setSrc] = useState("")

  useEffect(() => {
    let cancelled = false
    let objectUrl = ""
    if (!path) {
      setSrc("")
      return
    }

    const url = mediaUrl(path)
    const apiOrigin = API_BASE_URL || window.location.origin
    if (/^https?:\/\//i.test(url) && !url.startsWith(apiOrigin)) {
      setSrc(url)
      return
    }

    setSrc("")
    void apiFetch(url)
      .then(async response => {
        if (!response.ok) throw new Error("Image could not be loaded")
        return response.blob()
      })
      .then(blob => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setSrc(objectUrl)
      })
      .catch(() => {
        if (!cancelled) setSrc("")
      })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [path])

  if (!src) return null
  return <img {...imageProps} src={src} />
}
