import { BrowserRouter, Navigate, NavLink, Outlet, Route, Routes, useLocation, useNavigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"
import { NormsPage } from "./pages/NormsPage"
import { ProjectsPage } from "./pages/ProjectsPage"
import { PartsPage } from "./pages/PartsPage"
import { CostingSheetPage } from "./pages/CostingSheetPage"
import { ProjectSummaryPage } from "./pages/ProjectSummaryPage"
import { ClientsPage } from "./pages/ClientsPage"
import { DesktopActivationGate } from "./pages/DesktopActivationGate"
import { LoginPage } from "./pages/LoginPage"
import { ChangePasswordPage } from "./pages/ChangePasswordPage"
import { AuthProvider, useAuth } from "./auth"
import { cn } from "./lib/utils"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function signOut() {
    queryClient.clear()
    logout()
    navigate("/login", { replace: true })
  }

  return (
    <header className="min-h-14 flex items-center px-4 md:px-6 gap-2 shrink-0 z-10" style={{ background: "#111827", borderBottom: "1px solid #1e2a3a" }}>
      <div className="flex items-center mr-1">
        <img src="/smorx-logo.jpg" alt="SmorX.ai" className="h-9 w-auto rounded" style={{ imageRendering: "crisp-edges" }} />
      </div>
      <div className="w-px h-5 mx-1 md:mx-3" style={{ background: "rgba(255,255,255,0.12)" }} />
      <span className="text-sm font-semibold tracking-tight whitespace-nowrap" style={{ color: "rgba(255,255,255,0.75)" }}>
        Cost Sheet Studio
      </span>
      <div className="w-px h-5 mx-1 md:mx-3" style={{ background: "rgba(255,255,255,0.12)" }} />

      <nav className="flex items-center gap-0.5 overflow-x-auto">
        {[
          { to: "/clients", label: "Clients" },
          { to: "/workbooks", label: "Costing Workbooks" },
          { to: "/norms", label: "Norms Library" },
        ].map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => cn(
              "text-sm font-medium px-2 md:px-3 py-1.5 rounded-md transition-colors whitespace-nowrap",
              isActive ? "text-sky-300 bg-sky-400/15" : "text-slate-400 hover:text-white hover:bg-white/10",
            )}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="ml-auto flex items-center gap-3 pl-2">
        <span className="hidden lg:inline max-w-52 truncate text-xs" style={{ color: "rgba(255,255,255,0.55)" }} title={user?.email}>
          {user?.full_name || user?.email}
        </span>
        <button
          type="button"
          onClick={signOut}
          className="rounded-md border border-slate-600 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-slate-400 hover:bg-white/10"
        >
          Log out
        </button>
      </div>
    </header>
  )
}

function RequireAuth() {
  const { user } = useAuth()
  const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}

function RequirePasswordChanged() {
  const { user } = useAuth()
  if (user?.must_change_password) return <Navigate to="/change-password" replace />
  return <Outlet />
}

function AppRoutes() {
  const { user, ready } = useAuth()
  if (!ready) {
    return <main className="flex-1 grid place-items-center text-sm text-slate-500">Checking your sign-in…</main>
  }

  const homePath = user ? (user.must_change_password ? "/change-password" : "/clients") : "/login"

  return (
    <>
      {user && !user.must_change_password && <NavBar />}
      <main className="flex-1">
        <Routes>
          <Route path="/login" element={user ? <Navigate to={homePath} replace /> : <LoginPage />} />
          <Route element={<RequireAuth />}>
            <Route path="/change-password" element={user?.must_change_password ? <ChangePasswordPage /> : <Navigate to="/clients" replace />} />
            <Route element={<RequirePasswordChanged />}>
              <Route path="/" element={<Navigate to="/clients" replace />} />
              <Route path="/clients" element={<ClientsPage />} />
              <Route path="/workbooks" element={<ProjectsPage />} />
              <Route path="/workbooks/:workbookId/sheets" element={<PartsPage />} />
              <Route path="/workbooks/:workbookId/summary" element={<ProjectSummaryPage />} />
              <Route path="/sheets/:sheetId" element={<CostingSheetPage />} />
              <Route path="/norms" element={<NormsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to={homePath} replace />} />
        </Routes>
      </main>
    </>
  )
}

export default function App() {
  if (isTauriRuntime()) return <DesktopActivationGate />

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <div className="min-h-screen bg-slate-50 flex flex-col">
            <AppRoutes />
          </div>
        </AuthProvider>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  )
}

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" &&
    ("__TAURI_INTERNALS__" in window || "__TAURI__" in window)
}
