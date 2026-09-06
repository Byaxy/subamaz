import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useRestockPreview, useCreatePurchaseOrder, useWarehouses } from "@/lib/queries/parts"
import { useWarehouses as useWH } from "@/lib/queries/parts"
import { toast } from "sonner"

export const Route = createFileRoute("/parts/restock")({
  component: RestockPage,
})

function RestockPage() {
  const [warehouse, setWarehouse] = useState<string>("")
  const [step, setStep] = useState(1)
  const { data, isLoading, refetch } = useRestockPreview(warehouse || undefined)
  const warehouses = useWarehouses()
  const createPO = useCreatePurchaseOrder()
  const [created, setCreated] = useState<string[]>([])

  const lowItems: any[] = (data as any)?.low_items || []
  const groups: any[] = (data as any)?.groups || []

  const handleCreate = async () => {
    for (const g of groups) {
      try {
        const res: any = await createPO.mutateAsync({
          supplier: g.supplier !== "No Supplier" ? g.supplier : undefined,
          items: g.items.map((it: any) => ({ item_code: it.item_code, qty: it.qty_needed, warehouse: it.warehouse, rate: it.valuation_rate })) as any,
        } as any)
        setCreated((c) => [...c, res.name || g.supplier])
        toast.success(`PO for ${g.supplier} created`)
        // notify supplier via email stub — would use send_document modal path
      } catch (e: any) {
        toast.error(`PO for ${g.supplier} failed: ${e.message}`)
      }
    }
    setStep(3)
  }

  return (
    <div className="space-y-4" data-testid="restock-page">
      <h1 className="text-2xl font-bold">Restock — Auto Reorder</h1>
      <div className="flex gap-1">
        {[1, 2, 3].map((s) => (
          <div key={s} className={`h-1 flex-1 rounded ${s <= step ? "bg-[var(--app-primary)]" : "bg-muted"}`} />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            Step {step}: {step === 1 ? "Review Low Stock" : step === 2 ? "Preview Grouping" : "Create & Notify"}
          </CardTitle>
          <CardDescription>
            {step === 1 && "Items below reorder level — filterable by warehouse"}
            {step === 2 && "Group by preferred Supplier → one draft PO per supplier"}
            {step === 3 && "POs created — notify suppliers"}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex gap-2">
            <Label className="self-center">Warehouse</Label>
            <Select value={warehouse} onValueChange={setWarehouse}>
              <SelectTrigger className="w-64" data-testid="restock-warehouse">
                <SelectValue placeholder="All warehouses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All</SelectItem>
                {(warehouses.data || []).map((w: any) => (
                  <SelectItem key={w.name} value={w.name}>
                    {w.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => refetch()} data-testid="restock-refresh">
              Refresh
            </Button>
          </div>

          {step === 1 && (
            <div data-testid="step-1">
              {isLoading ? (
                <Skeleton className="h-32" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item</TableHead>
                      <TableHead>Warehouse</TableHead>
                      <TableHead>Actual</TableHead>
                      <TableHead>Reorder Level</TableHead>
                      <TableHead>Needed</TableHead>
                      <TableHead>Supplier</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {lowItems.map((it: any) => (
                      <TableRow key={`${it.item_code}-${it.warehouse}`} data-testid={`low-${it.item_code}`}>
                        <TableCell>{it.item_code}</TableCell>
                        <TableCell>{it.warehouse}</TableCell>
                        <TableCell>{it.actual_qty}</TableCell>
                        <TableCell>{it.reorder_level}</TableCell>
                        <TableCell>{it.qty_needed}</TableCell>
                        <TableCell>
                          <Badge>{it.supplier}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                    {lowItems.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">
                          No low stock
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
              <div className="mt-2 text-sm" data-testid="low-count">
                Low items: {lowItems.length} — Groups: {groups.length}
              </div>
            </div>
          )}

          {step === 2 && (
            <div data-testid="step-2">
              {groups.map((g: any) => (
                <Card key={g.supplier} className="mb-2">
                  <CardHeader className="py-2">
                    <CardTitle className="text-sm">
                      Supplier: {g.supplier} — {g.total_items} items
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Item</TableHead>
                          <TableHead>Qty Needed</TableHead>
                          <TableHead>Warehouse</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {g.items.map((it: any) => (
                          <TableRow key={it.item_code}>
                            <TableCell>{it.item_code}</TableCell>
                            <TableCell>{it.qty_needed}</TableCell>
                            <TableCell>{it.warehouse}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              ))}
              {groups.length === 0 && <div className="text-sm text-muted-foreground">No groups</div>}
            </div>
          )}

          {step === 3 && (
            <div data-testid="step-3">
              <div className="text-sm">Created POs: {created.length}</div>
              {created.map((c) => (
                <div key={c} className="text-sm">
                  {c}
                </div>
              ))}
              <div className="text-sm text-muted-foreground mt-2">Suppliers notified via email (demo)</div>
            </div>
          )}

          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(Math.max(1, step - 1))} disabled={step === 1}>
              Back
            </Button>
            {step < 3 ? (
              <Button
                onClick={() => setStep(step + 1)}
                disabled={step === 1 && lowItems.length === 0}
                data-testid="restock-next"
              >
                Next
              </Button>
            ) : (
              <Button onClick={handleCreate} disabled={groups.length === 0 || createPO.isPending} data-testid="restock-create">
                Create Purchase Orders
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
