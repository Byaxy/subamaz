import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useSupplierQuotations, useCreateSupplierQuotation, useCreatePurchaseOrder } from "@/lib/queries/procurement"
import { toast } from "sonner"
import { db } from "@/lib/frappe-client"

export const Route = createFileRoute("/procurement/supplier-quotations")({
  component: SupplierQuotationsPage,
})

function SupplierQuotationsPage() {
  const { data, isLoading } = useSupplierQuotations()
  const create = useCreateSupplierQuotation()
  const createPO = useCreatePurchaseOrder()
  const [form, setForm] = useState({ supplier: "", item_code: "", qty: "1", rate: "1000" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({
        supplier: form.supplier,
        items: [{ item_code: form.item_code, qty: parseFloat(form.qty), rate: parseFloat(form.rate) }] as any,
      } as any)
      toast.success("Supplier Quotation created")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  const handleConvert = async (name: string) => {
    try {
      const doc: any = await db.getDoc("Supplier Quotation", name)
      await createPO.mutateAsync({
        supplier: doc.supplier,
        items: doc.items,
      } as any)
      toast.success("Converted to Purchase Order")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="supplier-quotations-page">
      <h1 className="text-2xl font-bold">Supplier Quotations</h1>

      <Card>
        <CardHeader><CardTitle>Create</CardTitle></CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-4">
          <div><Label>Supplier</Label><Input value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} data-testid="sq-supplier" /></div>
          <div><Label>Item</Label><Input value={form.item_code} onChange={(e) => setForm({ ...form, item_code: e.target.value })} data-testid="sq-item" /></div>
          <div><Label>Qty</Label><Input value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} data-testid="sq-qty" /></div>
          <div><Label>Rate</Label><Input value={form.rate} onChange={(e) => setForm({ ...form, rate: e.target.value })} data-testid="sq-rate" /></div>
          <div className="md:col-span-4"><Button onClick={handleCreate} data-testid="create-sq">Create</Button></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>List</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Supplier</TableHead><TableHead>Status</TableHead><TableHead>Total</TableHead><TableHead>Convert</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`sq-${r.name}`}>
                    <TableCell>{r.name}</TableCell><TableCell>{r.supplier}</TableCell><TableCell>{r.status}</TableCell><TableCell>{r.grand_total}</TableCell>
                    <TableCell><Button size="sm" variant="outline" onClick={() => handleConvert(r.name)} data-testid={`convert-${r.name}`}>To PO</Button></TableCell>
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
