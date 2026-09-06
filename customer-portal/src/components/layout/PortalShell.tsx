import { useRouterState, Link, useNavigate } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { useLoggedUser, useLogout } from "@/lib/queries/auth"
import { LogOut, Car, FileText, History, Wallet } from "lucide-react"

export function PortalShell({ children }: { children: React.ReactNode }) {
  const routerState = useRouterState()
  const pathname = routerState.location.pathname
  const isLogin = pathname === "/login" || pathname.endsWith("/login")

  const { data: user, isLoading, isError } = useLoggedUser()
  const navigate = useNavigate()
  const logout = useLogout()

  if (isLogin) {
    return <>{children}</>
  }

  if (isLoading) {
    return <div className="p-6">Loading...</div>
  }

  if (isError || !user || user === "Guest") {
    navigate({ to: "/login" })
    return null
  }

  const handleLogout = async () => {
    await logout.mutateAsync()
    window.location.href = "/portal/login"
  }

  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b bg-white px-4 py-3 flex items-center justify-between">
        <Link to="/" className="font-bold flex items-center gap-2">
          <span className="size-8 rounded bg-[var(--app-primary)] text-white flex items-center justify-center">GM</span>
          Customer Portal
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link to="/" className="[&.active]:font-bold" activeOptions={{ exact: true }}>
            Vehicles
          </Link>
          <Link to="/history" className="[&.active]:font-bold">
            History
          </Link>
          <Link to="/invoices" className="[&.active]:font-bold">
            Invoices
          </Link>
        </nav>
        <Button variant="ghost" size="sm" onClick={handleLogout} data-testid="logout">
          <LogOut data-icon="inline-start" />
          Sign out
        </Button>
      </header>
      <main className="p-6 max-w-5xl mx-auto">{children}</main>
    </div>
  )
}
