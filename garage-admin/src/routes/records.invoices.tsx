import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useInvoices, useApplyDiscount, useVoidInvoice } from "@/lib/queries/money"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { DocumentModal } from "@/components/common/DocumentModal"
import { toast } from "sonner"

export const Route = createFileRoute("/records/invoices")({
  component: InvoicesPage,
})

function InvoicesPage() {
  const { data, isLoading } = useInvoices()
  const { data: caps } = useMyCapabilities()
  const apply = useApplyDiscount()
  const voidInv = useVoidInvoice()
  const [selected, setSelected] = useState<string | null>(null)
  const [discount, setDiscount] = useState("")
  const [docModal, setDocModal] = useState<{ open: boolean; name: string }>({ open: false, name: "" })

  const canDiscount = !!caps?.["action:apply_invoice_discount"]
  const canVoid = !!caps?.["action:void_invoice"]

  return (
    <div className="space-y-4" data-testid="invoices-page">
      <h1 className="text-2xl font-bold">Invoices</h1>

      <Card>
        <CardHeader><CardTitle>Sales Invoices — outstanding/payment status</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Customer</TableHead><TableHead>Total</TableHead><TableHead>Outstanding</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`inv-${r.name}`}>
                    <TableCell className="font-medium">{r.name}</TableCell><TableCell>{r.customer}</TableCell><TableCell>{r.grand_total}</TableCell><TableCell>{r.outstanding_amount}</TableCell><TableCell><Badge>{r.status}</Badge></TableCell>
                    <TableCell className="flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => setDocModal({ open: true, name: r.name })} data-testid={`inv-doc-${r.name}`}>Doc</Button>
                      <Button size="sm" variant="outline" onClick={() => setSelected(r.name)} data-testid={`inv-select-${r.name}`}>⋯</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selected && (
        <Card data-testid="invoice-actions">
          <CardHeader><CardTitle>Actions for {selected}</CardTitle></CardHeader>
          <CardContent className="flex gap-2 items-end">
            <div>
              <label className="text-sm">Discount</label>
              <Input value={discount} onChange={(e) => setDiscount(e.target.value)} placeholder="1000" data-testid="discount-input" />
            </div>
            {canDiscount ? (
              <Button onClick={async () => {
                try { await apply.mutateAsync({ invoice: selected, discount_amount: parseFloat(discount) }); toast.success("Discount applied") } catch (e: any) { toast.error(e.message) }
              }} data-testid="apply-discount">Apply Discount</Button>
            ) : (
              <Badge variant="outline">No discount capability</Badge>
            )}
            {canVoid ? (
              <Button variant="destructive" onClick={async () => {
                try { await voidInv.mutateAsync(selected); toast.success("Voided") } catch (e: any) { toast.error(e.message) }
              }} data-testid="void-invoice">Void</Button>
            ) : (
              <Badge variant="outline">No void capability</Badge>
            )}
          </CardContent>
        </Card>
      )}

      <DocumentModal open={docModal.open} onOpenChange={(open) => setDocModal({ ...docModal, open })} doctype="Sales Invoice" name={docModal.name} />
    </div>
  )
}
