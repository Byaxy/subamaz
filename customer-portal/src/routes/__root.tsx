import { Outlet, createRootRouteWithContext } from "@tanstack/react-router"
import { QueryClient } from "@tanstack/react-query"
import { Toaster } from "@/components/ui/sonner"
import { PortalShell } from "@/components/layout/PortalShell"

type RouterContext = {
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
})

function RootComponent() {
  return (
    <>
      <PortalShell>
        <Outlet />
      </PortalShell>
      <Toaster />
    </>
  )
}
