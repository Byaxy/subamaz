import { createFileRoute, Link } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useMyVehicles } from "@/lib/queries/portal"

export const Route = createFileRoute("/")({
  component: DashboardPage,
})

function DashboardPage() {
  const { data, isLoading, isError } = useMyVehicles()

  if (isLoading) return <Skeleton className="h-32" />
  if (isError) return <div className="text-sm text-destructive">Failed to load vehicles</div>

  const vehicles: any[] = (data as any)?.message || (data as any) || []

  return (
    <div className="space-y-4" data-testid="portal-dashboard">
      <h1 className="text-2xl font-bold">My Vehicles</h1>
      {(vehicles || []).length === 0 && <div className="text-sm text-muted-foreground">No vehicles</div>}
      <div className="grid gap-4 md:grid-cols-2">
        {(vehicles || []).map((v: any) => (
          <Card key={v.name} data-testid={`vehicle-${v.name}`}>
            <CardHeader>
              <CardTitle>{v.registration_number} — {v.make} {v.model}</CardTitle>
              <Badge>{v.current_status}</Badge>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Link to="/vehicle/$vehicleId" params={{ vehicleId: v.name }} className="text-sm text-primary underline">
                View
              </Link>
              {v.current_service_order && (
                <Link to="/service-order/$name" params={{ name: v.current_service_order }} className="text-sm text-primary underline">
                  Service Order
                </Link>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
