import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useCustomerStatement } from "@/lib/queries/money"
import { useCustomers } from "@/lib/queries/customers"

export const Route = createFileRoute("/records/customer-statement")({
  component: StatementPage,
})

function StatementPage() {
  const [customer, setCustomer] = useState("")
  const customers = useCustomers()
  const { data, isLoading, refetch } = useCustomerStatement(customer)

  return (
    <div className="space-y-4" data-testid="statement-page">
      <h1 className="text-2xl font-bold">Customer Statement</h1>

      <Card>
        <CardHeader><CardTitle>Per-customer summary — reuses Customer Statement Summary report</CardTitle></CardHeader>
        <CardContent className="flex gap-2">
          <div className="flex-1">
            <Label>Customer</Label>
            <select value={customer} onChange={(e) => setCustomer(e.target.value)} className="w-full border rounded p-2" data-testid="stmt-customer">
              <option value="">Select</option>
              {(customers.data || []).map((c: any) => (
                <option key={c.name} value={c.name}>{c.customer_name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <Button onClick={() => refetch()} data-testid="stmt-run">Run</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Statement</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Customer</TableHead><TableHead>Invoices</TableHead><TableHead>Billed</TableHead><TableHead>Outstanding</TableHead></TableRow></TableHeader>
              <TableBody>
                {((data as any)?.result || (data as any)?.rows || []).map((r: any, i: number) => (
                  <TableRow key={i} data-testid={`stmt-row-${i}`}>
                    <TableCell>{r.customer}</TableCell><TableCell>{r.invoices}</TableCell><TableCell>{r.billed}</TableCell><TableCell>{r.outstanding}</TableCell>
                  </TableRow>
                ))}
                {(!data || ((data as any)?.result || []).length === 0) && (
                  <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No data — select customer and Run</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          )}
          <div className="flex gap-2 mt-4">
            <Button variant="outline" onClick={() => window.print()} data-testid="stmt-export">Export</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
