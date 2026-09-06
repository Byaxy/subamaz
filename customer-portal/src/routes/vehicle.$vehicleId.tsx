import { createFileRoute, Link } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useVehicleDetail } from "@/lib/queries/portal"

export const Route = createFileRoute("/vehicle/$vehicleId")({
  component: VehiclePage,
})

function VehiclePage() {
  const { vehicleId } = Route.useParams()
  const { data, isLoading } = useVehicleDetail(vehicleId)

  if (isLoading) return <Skeleton className="h-32" />
  const v: any = (data as any)?.message || data

  return (
    <div className="space-y-4" data-testid="vehicle-detail">
      <h1 className="text-2xl font-bold">{v?.registration_number} — {v?.make} {v?.model}</h1>
      <Card>
        <CardHeader><CardTitle>Vehicle</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-1">
          <div>VIN: {v?.vin}</div>
          <div>Status: <Badge>{v?.current_status}</Badge></div>
          <div>Mileage: {v?.current_mileage}</div>
          {v?.current_service_order && <Link to="/service-order/$name" params={{ name: v.current_service_order }} className="text-primary underline">Current Service Order: {v.current_service_order}</Link>}
        </CardContent>
      </Card>
      <Link to="/history" className="text-sm text-primary underline">View History</Link>
    </div>
  )
}
