import { createFileRoute, Link } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useMyInvoices } from "@/lib/queries/portal"

export const Route = createFileRoute("/invoices")({
  component: InvoicesPage,
})

function InvoicesPage() {
  const { data, isLoading } = useMyInvoices()
  const invoices: any[] = (data as any)?.message || (data as any) || []

  return (
    <div className="space-y-4" data-testid="invoices-page">
      <h1 className="text-2xl font-bold">My Invoices</h1>
      <Card>
        <CardHeader><CardTitle>Invoices</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Posting</TableHead><TableHead>Total</TableHead><TableHead>Outstanding</TableHead><TableHead>Status</TableHead><TableHead>Pay</TableHead></TableRow></TableHeader>
              <TableBody>
                {invoices.map((inv: any) => (
                  <TableRow key={inv.name} data-testid={`invoice-${inv.name}`}>
                    <TableCell>{inv.name}</TableCell><TableCell>{inv.posting_date}</TableCell><TableCell>{inv.grand_total}</TableCell><TableCell>{inv.outstanding_amount}</TableCell><TableCell><Badge>{inv.status}</Badge></TableCell>
                    <TableCell>{inv.outstanding_amount > 0 ? <Link to="/invoices/$name/pay" params={{ name: inv.name }} className="text-primary underline">Pay</Link> : "Paid"}</TableCell>
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
