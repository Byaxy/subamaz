import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useServiceOrders, useServiceOrder } from "@/lib/queries/service"
import { useState } from "react"
import { db } from "@/lib/frappe-client"
import { toast } from "sonner"

export const Route = createFileRoute("/service/orders")({
  component: OrdersPage,
})

function OrdersPage() {
  const { data, isLoading } = useServiceOrders()
  const [selected, setSelected] = useState<string | null>(null)
  const order = useServiceOrder(selected || "")

  const handleTransition = async (status: string) => {
    if (!selected) return
    try {
      await db.updateDoc("Service Order", selected, { status } as any)
      toast.success(`Moved to ${status}`)
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="orders-page">
      <h1 className="text-2xl font-bold">Service Orders</h1>

      <Card>
        <CardHeader>
          <CardTitle>List</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Completion</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow
                    key={r.name}
                    data-testid={`order-${r.name}`}
                    className="cursor-pointer"
                    onClick={() => setSelected(r.name)}
                  >
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.customer}</TableCell>
                    <TableCell>{r.vehicle}</TableCell>
                    <TableCell>
                      <Badge>{r.status}</Badge>
                    </TableCell>
                    <TableCell>{r.completion_percent || 0}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selected && order.data && (
        <Card data-testid="order-detail">
          <CardHeader>
            <CardTitle>{order.data.name} — {order.data.status}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <div className="text-sm">
              <div>Customer: {order.data.customer}</div>
              <div>Vehicle: {order.data.vehicle}</div>
              <div>Diagnosis: {order.data.diagnosis}</div>
              <div>Estimated: {order.data.estimated_total}</div>
              <div>Actual: {order.data.actual_total}</div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {["Open", "Waiting Customer", "Waiting Parts", "In Progress", "Quality Check", "Completed", "Closed"].map((s) => (
                <Button key={s} size="sm" variant="outline" onClick={() => handleTransition(s)} data-testid={`transition-${s}`}>
                  {s}
                </Button>
              ))}
            </div>
            <div>
              <h4 className="font-medium">Timeline</h4>
              {(order.data.timeline || []).map((t: any, i: number) => (
                <div key={i} className="text-xs border-b py-1">
                  {t.timestamp} — {t.event_type}: {t.description} {t.visible_to_customer ? "(visible)" : ""}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
