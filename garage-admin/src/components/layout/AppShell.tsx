import { useRouterState, Link, useNavigate } from "@tanstack/react-router"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { Sidebar } from "./Sidebar"
import { GlobalSearch } from "../common/GlobalSearch"
import { Button } from "../ui/button"
import { Skeleton } from "../ui/skeleton"
import { useLogout } from "@/lib/queries/auth"
import { LogOut } from "lucide-react"

export function AppShell({ children }: { children: React.ReactNode }) {
  const routerState = useRouterState()
  const pathname = routerState.location.pathname
  const isLogin = pathname === "/login" || pathname.endsWith("/login")

  if (isLogin) {
    return <>{children}</>
  }

  const { data: capabilities, isLoading, isError } = useMyCapabilities()
  const navigate = useNavigate()
  const logout = useLogout()

  if (isLoading) {
    return (
      <div className="flex h-screen">
        <div className="w-64 border-r p-4">
          <Skeleton className="h-6 w-32 mb-4" />
          <Skeleton className="h-8 w-full mb-2" />
          <Skeleton className="h-8 w-full mb-2" />
        </div>
        <div className="flex-1 p-6">{children}</div>
      </div>
    )
  }

  if (isError || !capabilities) {
    // likely Guest — redirect to login
    navigate({ to: "/login" })
    return null
  }

  const handleLogout = async () => {
    await logout.mutateAsync()
    window.location.href = "/garage/login"
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar capabilities={capabilities} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header
          className="flex h-14 items-center gap-4 border-b px-4"
          style={{ background: "var(--app-navbar-bg)", color: "var(--app-navbar-text)" }}
        >
          <div className="flex-1 max-w-xl">
            <GlobalSearch />
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleLogout} data-testid="logout-button">
              <LogOut data-icon="inline-start" />
              Sign out
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-auto bg-muted/20 p-6">{children}</main>
      </div>
    </div>
  )
}

// Re-export for root
export default AppShell
