import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { usePurchaseOrders } from "@/lib/queries/procurement"
import { db } from "@/lib/frappe-client"
import { toast } from "sonner"

export const Route = createFileRoute("/procurement/purchase-orders")({
  component: PurchaseOrdersPage,
})

function PurchaseOrdersPage() {
  const { data, isLoading } = usePurchaseOrders()

  const handleReceive = async (name: string) => {
    try {
      const po: any = await db.getDoc("Purchase Order", name)
      // Create Purchase Receipt from PO via stock
      await db.createDoc("Purchase Receipt", { supplier: po.supplier, items: po.items } as any)
      toast.success("Purchase Receipt created")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="purchase-orders-page">
      <h1 className="text-2xl font-bold">Purchase Orders</h1>

      <Card>
        <CardHeader><CardTitle>List</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Supplier</TableHead><TableHead>Status</TableHead><TableHead>Total</TableHead><TableHead>Receive</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`po-${r.name}`}>
                    <TableCell>{r.name}</TableCell><TableCell>{r.supplier}</TableCell><TableCell><Badge>{r.status}</Badge></TableCell><TableCell>{r.grand_total}</TableCell>
                    <TableCell><Button size="sm" variant="outline" onClick={() => handleReceive(r.name)} data-testid={`receive-${r.name}`}>Receive</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
