import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { useServiceOrderProgress, useCustomerTimeline } from "@/lib/queries/portal"

export const Route = createFileRoute("/service-order/$name")({
  component: ServiceOrderPage,
})

function ServiceOrderPage() {
  const { name } = Route.useParams()
  const progress = useServiceOrderProgress(name)
  const timeline = useCustomerTimeline(name)

  if (progress.isLoading) return <Skeleton className="h-32" />
  const p: any = (progress.data as any)?.message || progress.data

  return (
    <div className="space-y-4" data-testid="service-order-page">
      <h1 className="text-2xl font-bold">Service Order {name}</h1>
      <Card>
        <CardHeader><CardTitle>Progress</CardTitle></CardHeader>
        <CardContent>
          <div className="text-sm">Completion: {p?.completion_percent || 0}%</div>
          <Progress value={p?.completion_percent || 0} className="mt-2" />
          <div className="text-sm mt-2">Status: <Badge>{p?.status}</Badge></div>
          <div className="text-sm">Estimated: {p?.estimated_total} — Actual: {p?.actual_total}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Timeline (customer-visible)</CardTitle></CardHeader>
        <CardContent>
          {(timeline.data as any)?.message ? (timeline.data as any).message.map((t: any, i: number) => (
            <div key={i} className="border-b py-2 text-sm"><div className="font-medium">{t.event_type}: {t.description}</div><div className="text-xs text-muted-foreground">{t.timestamp}</div></div>
          )) : (timeline.data as any || []).map((t: any, i: number) => (
            <div key={i} className="border-b py-2 text-sm"><div className="font-medium">{t.event_type}: {t.description}</div><div className="text-xs text-muted-foreground">{t.timestamp}</div></div>
          ))}
          {(!timeline.data || (Array.isArray(timeline.data) && timeline.data.length === 0)) && <div className="text-sm text-muted-foreground">No timeline</div>}
        </CardContent>
      </Card>
    </div>
  )
}
