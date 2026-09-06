import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useQuotations } from "@/lib/queries/money"
import { DocumentModal } from "@/components/common/DocumentModal"
import { useState } from "react"

export const Route = createFileRoute("/records/quotations")({
  component: QuotationsPage,
})

function QuotationsPage() {
  const { data, isLoading } = useQuotations()
  const [docModal, setDocModal] = useState<{ open: boolean; name: string }>({ open: false, name: "" })

  return (
    <div className="space-y-4" data-testid="quotations-page">
      <h1 className="text-2xl font-bold">Quotations</h1>

      <Card>
        <CardHeader><CardTitle>List — review/approve states</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Customer</TableHead><TableHead>Status</TableHead><TableHead>Total</TableHead><TableHead>Send</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`quo-${r.name}`}>
                    <TableCell>{r.name}</TableCell><TableCell>{r.customer_name}</TableCell><TableCell><Badge>{r.status}</Badge></TableCell><TableCell>{r.grand_total}</TableCell>
                    <TableCell><Button size="sm" variant="outline" onClick={() => setDocModal({ open: true, name: r.name })} data-testid={`quo-doc-${r.name}`}>Send</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <DocumentModal open={docModal.open} onOpenChange={(open) => setDocModal({ ...docModal, open })} doctype="Quotation" name={docModal.name} />
    </div>
  )
}
