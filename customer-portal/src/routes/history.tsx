import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useServiceHistory } from "@/lib/queries/portal"

export const Route = createFileRoute("/history")({
  component: HistoryPage,
})

function HistoryPage() {
  const { data, isLoading } = useServiceHistory()
  const history: any[] = (data as any)?.message || (data as any) || []

  return (
    <div className="space-y-4" data-testid="history-page">
      <h1 className="text-2xl font-bold">Service History</h1>
      <Card>
        <CardHeader><CardTitle>All vehicles</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <div className="space-y-2">
              {history.map((h: any, i: number) => (
                <div key={i} className="border-b py-2 text-sm" data-testid={`history-${h.doctype}-${h.name}`}>
                  <div className="font-medium">{h.title} — {h.doctype}</div><div className="text-muted-foreground">{h.description}</div><div className="text-xs">{h.date}</div>
                </div>
              ))}
              {history.length === 0 && <div className="text-sm text-muted-foreground">No history</div>}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
