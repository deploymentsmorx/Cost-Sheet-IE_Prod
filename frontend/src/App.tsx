import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"
import { NormsPage } from "./pages/NormsPage"
import { ProjectsPage } from "./pages/ProjectsPage"
import { PartsPage } from "./pages/PartsPage"
import { CostingSheetPage } from "./pages/CostingSheetPage"
import { ProjectSummaryPage } from "./pages/ProjectSummaryPage"
import { ClientsPage } from "./pages/ClientsPage"
import { DesktopActivationGate } from "./pages/DesktopActivationGate"
import { cn } from "./lib/utils"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

function NavBar() {
  return (
    <header className="h-14 flex items-center px-6 gap-2 shrink-0 z-10" style={{ background: "#111827", borderBottom: "1px solid #1e2a3a" }}>
      {/* SmorX Logo */}
      <div className="flex items-center mr-1">
        <img
          src="/smorx-logo.jpg"
          alt="SmorX.ai"
          className="h-9 w-auto rounded"
          style={{ imageRendering: "crisp-edges" }}
        />
      </div>

      {/* App name separator */}
      <div className="w-px h-5 mx-3" style={{ background: "rgba(255,255,255,0.12)" }} />
      <span className="text-sm font-semibold tracking-tight" style={{ color: "rgba(255,255,255,0.75)" }}>
        Cost Sheet Studio
      </span>

      <div className="w-px h-5 mx-3" style={{ background: "rgba(255,255,255,0.12)" }} />

      <nav className="flex items-center gap-0.5">
        {[
          { to: "/clients",   label: "Clients" },
          { to: "/workbooks", label: "Costing Workbooks" },
          { to: "/norms",     label: "Norms Library" },
        ].map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "text-sm font-medium px-3 py-1.5 rounded-md transition-colors",
                isActive
                  ? "text-sky-300 bg-sky-400/15"
                  : "text-slate-400 hover:text-white hover:bg-white/10"
              )
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="ml-auto text-xs select-none" style={{ color: "rgba(255,255,255,0.3)" }}>
        © SmorX.ai
      </div>
    </header>
  )
}

export default function App() {
  if (isTauriRuntime()) return <DesktopActivationGate />

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-50 flex flex-col">
          <NavBar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Navigate to="/clients" replace />} />
              <Route path="/clients" element={<ClientsPage />} />
              <Route path="/workbooks" element={<ProjectsPage />} />
              <Route path="/workbooks/:workbookId/sheets" element={<PartsPage />} />
              <Route path="/workbooks/:workbookId/summary" element={<ProjectSummaryPage />} />
              <Route path="/sheets/:sheetId" element={<CostingSheetPage />} />
              <Route path="/norms" element={<NormsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  )
}

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" &&
    ("__TAURI_INTERNALS__" in window || "__TAURI__" in window)
}
