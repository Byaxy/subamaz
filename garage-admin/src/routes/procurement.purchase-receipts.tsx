import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { usePurchaseReceipts } from "@/lib/queries/procurement"

export const Route = createFileRoute("/procurement/purchase-receipts")({
  component: PurchaseReceiptsPage,
})

function PurchaseReceiptsPage() {
  const { data, isLoading } = usePurchaseReceipts()

  return (
    <div className="space-y-4" data-testid="purchase-receipts-page">
      <h1 className="text-2xl font-bold">Purchase Receipts</h1>

      <Card>
        <CardHeader><CardTitle>List — stock entry from PO receipt</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Supplier</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`pr-${r.name}`}>
                    <TableCell>{r.name}</TableCell><TableCell>{r.supplier}</TableCell><TableCell>{r.status}</TableCell>
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
