import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useVehicle, useVehicleHistory } from "@/lib/queries/customers"

export const Route = createFileRoute("/vehicles/$vehicleId/history")({
  component: HistoryPage,
})

function HistoryPage() {
  const { vehicleId } = Route.useParams()
  const vehicle = useVehicle(vehicleId)
  const history = useVehicleHistory(vehicleId)

  return (
    <div className="space-y-4" data-testid="history-page">
      <h1 className="text-2xl font-bold">Vehicle History — {vehicleId}</h1>
      {vehicle.data && <div className="text-sm text-muted-foreground">{vehicle.data.registration_number} • {vehicle.data.customer}</div>}

      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          {history.isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <div className="space-y-2">
              {(history.data || []).map((h: any, i: number) => (
                <div key={i} className="flex gap-3 border-b py-2" data-testid={`history-${h.doctype}-${h.name}`}>
                  <div className="text-xs text-muted-foreground w-32">{h.date}</div>
                  <div className="flex-1">
                    <div className="font-medium text-sm flex items-center gap-2">
                      {h.title} <Badge variant={h.visible_to_customer ? "secondary" : "outline"}>{h.visible_to_customer ? "customer" : "internal"}</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">{h.description}</div>
                    <div className="text-xs">{h.doctype} {h.name}</div>
                  </div>
                </div>
              ))}
              {(!history.data || history.data.length === 0) && <div className="text-sm text-muted-foreground">No history</div>}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
