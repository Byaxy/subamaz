import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useJobCards, useJobCard, useJobCardActions } from "@/lib/queries/service"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"

export const Route = createFileRoute("/service/job-cards")({
  component: JobCardsPage,
})

const COLUMNS = ["Assigned", "Working", "Paused", "Waiting Parts", "Waiting Approval", "Ready QA", "Completed"]

function JobCardsPage() {
  const { data, isLoading } = useJobCards()
  const [selected, setSelected] = useState<string | null>(null)
  const jobCard = useJobCard(selected || "")
  const actions = useJobCardActions()
  const [consume, setConsume] = useState({ item_code: "", qty: "1", warehouse: "" })

  const handleAction = async (act: "start" | "pause" | "complete") => {
    if (!selected) return
    try {
      if (act === "start") await actions.start.mutateAsync(selected)
      if (act === "pause") await actions.pause.mutateAsync(selected)
      if (act === "complete") await actions.complete.mutateAsync(selected)
      toast.success(`${act} ok`)
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  const handleConsume = async () => {
    if (!selected) return
    try {
      await actions.consume.mutateAsync({ job_card: selected, item_code: consume.item_code, qty: parseFloat(consume.qty), warehouse: consume.warehouse || undefined } as any)
      toast.success("Consumed")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="job-cards-page">
      <h1 className="text-2xl font-bold">Job Cards — Kanban</h1>

      {isLoading ? (
        <Skeleton className="h-64" />
      ) : (
        <div className="grid gap-2 md:grid-cols-4 lg:grid-cols-7 overflow-auto">
          {COLUMNS.map((col) => (
            <div key={col} className="border rounded bg-muted/20 min-h-64" data-testid={`col-${col}`}>
              <div className="p-2 font-medium text-sm border-b bg-[var(--app-table-header-bg)] text-[var(--app-table-header-text)] rounded-t">
                {col}
              </div>
              <div className="p-2 flex flex-col gap-2">
                {(data || [])
                  .filter((j: any) => j.status === col)
                  .map((j: any) => (
                    <Card key={j.name} className="cursor-pointer hover:shadow" onClick={() => setSelected(j.name)} data-testid={`job-${j.name}`}>
                      <CardContent className="p-3">
                        <div className="font-medium text-sm">{j.name}</div>
                        <div className="text-xs text-muted-foreground">{j.service_order}</div>
                        <div className="text-xs">{j.department}</div>
                        <Badge variant="secondary" className="mt-1">
                          {j.completion_percent || 0}%
                        </Badge>
                      </CardContent>
                    </Card>
                  ))}
                {(data || []).filter((j: any) => j.status === col).length === 0 && <div className="text-xs text-muted-foreground p-2">Empty</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto" data-testid="job-detail">
          <DialogHeader>
            <DialogTitle>{jobCard.data?.name} — {jobCard.data?.status}</DialogTitle>
          </DialogHeader>
          {jobCard.data && (
            <div className="flex flex-col gap-2">
              <div className="text-sm">
                <div>Service Order: {jobCard.data.service_order}</div>
                <div>Department: {jobCard.data.department}</div>
                <div>Lead: {jobCard.data.lead_technician}</div>
                <div>Hours: {jobCard.data.actual_hours} / Cost: {jobCard.data.actual_cost}</div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => handleAction("start")} data-testid="job-start">
                  Start
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleAction("pause")} data-testid="job-pause">
                  Pause
                </Button>
                <Button size="sm" variant="secondary" onClick={() => handleAction("complete")} data-testid="job-complete">
                  Complete → Ready QA
                </Button>
              </div>

              <div>
                <h4 className="font-medium text-sm">Time Logs</h4>
                {(jobCard.data.time_logs || []).map((t: any, i: number) => (
                  <div key={i} className="text-xs border p-1 rounded">
                    {t.technician} — {t.hours}h @ {t.hourly_rate} = {t.labour_cost}
                  </div>
                ))}
              </div>

              <div>
                <h4 className="font-medium text-sm">Consumed Parts</h4>
                {(jobCard.data.consumed_parts || []).map((c: any, i: number) => (
                  <div key={i} className="text-xs border p-1 rounded">
                    {c.item_code} x {c.qty} = {c.amount}
                  </div>
                ))}
                <div className="flex gap-2 mt-2">
                  <Input placeholder="Item Code" value={consume.item_code} onChange={(e) => setConsume({ ...consume, item_code: e.target.value })} data-testid="consume-item" />
                  <Input placeholder="Qty" value={consume.qty} onChange={(e) => setConsume({ ...consume, qty: e.target.value })} className="w-20" data-testid="consume-qty" />
                  <Input placeholder="Warehouse" value={consume.warehouse} onChange={(e) => setConsume({ ...consume, warehouse: e.target.value })} data-testid="consume-wh" />
                  <Button size="sm" onClick={handleConsume} data-testid="consume-btn">
                    Consume
                  </Button>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-sm">QA Checklist</h4>
                {(jobCard.data.quality_checklist || []).map((q: any, i: number) => (
                  <div key={i} className="text-xs">
                    {q.checklist_item}: {q.result}
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
