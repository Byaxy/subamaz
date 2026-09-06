import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useReceptionRecord } from "@/lib/queries/portal"

export const Route = createFileRoute("/reception/$name")({
  component: ReceptionPage,
})

function ReceptionPage() {
  const { name } = Route.useParams()
  const { data, isLoading } = useReceptionRecord(name)
  const r: any = (data as any)?.message || data

  if (isLoading) return <Skeleton className="h-32" />

  return (
    <div className="space-y-4" data-testid="reception-page">
      <h1 className="text-2xl font-bold">Reception {name}</h1>
      <Card>
        <CardHeader><CardTitle>Read-only intake record</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-1">
          <div>Vehicle: {r?.vehicle}</div>
          <div>Customer: {r?.customer}</div>
          <div>Complaint: {r?.customer_complaint}</div>
          <div>Fuel: {r?.fuel_level} — Battery: {r?.battery_condition}</div>
          <div>Odometer: {r?.odometer_reading}</div>
          <div>Status: {r?.status}</div>
        </CardContent>
      </Card>
    </div>
  )
}
