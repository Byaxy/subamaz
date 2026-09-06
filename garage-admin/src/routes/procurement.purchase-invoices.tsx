import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { usePurchaseInvoices } from "@/lib/queries/procurement"

export const Route = createFileRoute("/procurement/purchase-invoices")({
  component: PurchaseInvoicesPage,
})

function PurchaseInvoicesPage() {
  const { data, isLoading } = usePurchaseInvoices()

  return (
    <div className="space-y-4" data-testid="purchase-invoices-page">
      <h1 className="text-2xl font-bold">Purchase Invoices</h1>

      <Card>
        <CardHeader><CardTitle>List</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Supplier</TableHead><TableHead>Status</TableHead><TableHead>Total</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`pi-${r.name}`}>
                    <TableCell>{r.name}</TableCell><TableCell>{r.supplier}</TableCell><TableCell>{r.status}</TableCell><TableCell>{r.grand_total}</TableCell>
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
