import { useEffect, useState, type CSSProperties, type FormEvent, type ReactNode } from "react"
import { invoke } from "@tauri-apps/api/core"

export const COSTSHEET_URL = "http://100.51.165.76:28080"

type DeviceInfo = { deviceId: string; hostname: string }

type ActivationRequest = {
  licenseKey: string
  installPassword: string
  username: string
  password: string
  deviceId: string
  hostname: string
}

export function DesktopActivationGate({ children }: { children: ReactNode }) {
  const [device, setDevice] = useState<DeviceInfo | null>(null)
  const [licenseKey, setLicenseKey] = useState("")
  const [installPassword, setInstallPassword] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [checking, setChecking] = useState(true)
  const [authorized, setAuthorized] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function initialize() {
      try {
        const info = await invoke<DeviceInfo>("get_device_info")
        if (cancelled) return
        setDevice(info)

        try {
          const activated = await invoke<boolean>("check_costsheet_activation", {
            deviceId: info.deviceId,
          })
          if (!cancelled && activated) {
            if (window.location.origin === new URL(COSTSHEET_URL).origin) setAuthorized(true)
            else window.location.replace(COSTSHEET_URL)
          }
          else if (!cancelled) setChecking(false)
        } catch (ex) {
          if (!cancelled) {
            setError(`Could not check activation with the license server: ${messageOf(ex)}`)
            setChecking(false)
          }
        }
      } catch (ex) {
        if (!cancelled) {
          setError(`Could not read this computer's device ID: ${messageOf(ex)}`)
          setChecking(false)
        }
      }
    }

    void initialize()
    return () => { cancelled = true }
  }, [])

  async function activate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!device || busy) return
    setBusy(true)
    setError("")

    const request: ActivationRequest = {
      licenseKey: licenseKey.trim(),
      installPassword,
      username: username.trim(),
      password,
      deviceId: device.deviceId,
      hostname: device.hostname,
    }

    try {
      const token = await invoke<string>("activate_costsheet", { request })
      window.location.replace(`${COSTSHEET_URL}/#costsheet_token=${encodeURIComponent(token)}`)
    } catch (ex) {
      setError(messageOf(ex))
      setBusy(false)
    }
  }

  if (authorized) return <>{children}</>

  if (checking) {
    return <div style={styles.screen}><div style={styles.card}>Checking Cost Sheet license…</div></div>
  }

  return (
    <div style={styles.screen}>
      <section style={styles.card}>
        <div style={styles.brand}>SMORX <span>•</span> COST SHEET</div>
        <h1 style={styles.title}>Activate Cost Sheet</h1>
        <p style={styles.copy}>
          Enter the license and sign-in details provided by your administrator. This activation is for this computer.
        </p>

        {error && <div role="alert" style={styles.error}>{error}</div>}

        <div style={styles.deviceBox}>
          <div style={styles.deviceLabel}>This computer’s device ID</div>
          <code style={styles.deviceId}>{device?.deviceId ?? "Unavailable"}</code>
          <div style={styles.hostname}>Computer name: {device?.hostname ?? "Unavailable"}</div>
        </div>

        <form onSubmit={activate} style={styles.form}>
          <label style={styles.label}>
            License key
            <input required autoComplete="off" value={licenseKey} onChange={e => setLicenseKey(e.target.value)} style={styles.input} />
          </label>
          <label style={styles.label}>
            Install password
            <input required type="password" autoComplete="new-password" value={installPassword} onChange={e => setInstallPassword(e.target.value)} style={styles.input} />
          </label>
          <label style={styles.label}>
            Engineer email or username
            <input required autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} style={styles.input} />
          </label>
          <label style={styles.label}>
            Temporary password
            <input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} style={styles.input} />
          </label>
          <button type="submit" disabled={!device || busy} style={{ ...styles.button, opacity: !device || busy ? 0.65 : 1 }}>
            {busy ? "Activating…" : "Activate and open Cost Sheet"}
          </button>
        </form>
        <p style={styles.footer}>Need access? Contact your Cost Sheet administrator.</p>
      </section>
    </div>
  )
}

function messageOf(error: unknown): string {
  if (typeof error === "string") return error
  return error instanceof Error ? error.message : "Activation failed. Please try again."
}

const styles: Record<string, CSSProperties> = {
  screen: {
    minHeight: "100vh", display: "grid", placeItems: "center", padding: 24,
    background: "linear-gradient(135deg, #f1f5f9 0%, #e0f2fe 100%)", color: "#0f172a",
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  card: {
    width: "min(100%, 460px)", padding: 32, borderRadius: 18, background: "white",
    boxShadow: "0 22px 60px rgba(15, 23, 42, 0.14)", border: "1px solid #e2e8f0",
  },
  brand: { color: "#0f766e", fontWeight: 800, letterSpacing: ".11em", fontSize: 12 },
  title: { margin: "14px 0 8px", fontSize: 28, letterSpacing: "-.03em" },
  copy: { color: "#64748b", lineHeight: 1.55, margin: "0 0 22px" },
  error: { background: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca", borderRadius: 9, padding: 12, marginBottom: 16, lineHeight: 1.45 },
  deviceBox: { background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10, padding: 13, marginBottom: 18 },
  deviceLabel: { color: "#64748b", fontSize: 12, marginBottom: 5 },
  deviceId: { display: "block", overflowWrap: "anywhere", fontSize: 12, color: "#0f172a", userSelect: "text" },
  hostname: { color: "#64748b", fontSize: 12, marginTop: 5 },
  form: { display: "grid", gap: 13 },
  label: { display: "grid", gap: 6, color: "#334155", fontSize: 13, fontWeight: 600 },
  input: { width: "100%", boxSizing: "border-box", padding: "10px 11px", border: "1px solid #cbd5e1", borderRadius: 8, fontSize: 14, outlineColor: "#0ea5e9" },
  button: { border: 0, borderRadius: 9, background: "#0f766e", color: "white", padding: "12px 16px", marginTop: 4, fontSize: 14, fontWeight: 700, cursor: "pointer" },
  footer: { margin: "18px 0 0", color: "#94a3b8", fontSize: 12, textAlign: "center" },
}
