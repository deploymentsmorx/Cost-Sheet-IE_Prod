import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../auth"

export function ChangePasswordPage() {
  const { changePassword, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    if (newPassword !== confirmPassword) {
      setError("The new passwords do not match.")
      return
    }
    setBusy(true)
    try {
      await changePassword(currentPassword, newPassword)
      await refreshUser()
      navigate("/clients", { replace: true })
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Password update failed.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="min-h-screen grid place-items-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Set your password</h1>
        <p className="mt-2 text-sm text-slate-500">For security, replace the temporary password before continuing.</p>
        <form onSubmit={submit} className="mt-7 space-y-5">
          <label className="block text-sm font-medium text-slate-700">
            Temporary password
            <input required type="password" autoComplete="current-password" value={currentPassword} onChange={event => setCurrentPassword(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100" />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            New password
            <input required minLength={8} type="password" autoComplete="new-password" value={newPassword} onChange={event => setNewPassword(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100" />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Confirm new password
            <input required minLength={8} type="password" autoComplete="new-password" value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100" />
          </label>
          {error && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">{error}</p>}
          <button type="submit" disabled={busy} className="w-full rounded-lg bg-sky-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-wait disabled:opacity-60">
            {busy ? "Saving…" : "Save password"}
          </button>
        </form>
      </section>
    </main>
  )
}
