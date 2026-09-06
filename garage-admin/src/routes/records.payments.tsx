import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { usePayments, useCreatePayment } from "@/lib/queries/money"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { call } from "@/lib/frappe-client"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"

export const Route = createFileRoute("/records/payments")({
  component: PaymentsPage,
})

function PaymentsPage() {
  const { data, isLoading } = usePayments()
  const create = useCreatePayment()
  const { data: caps } = useMyCapabilities()
  const canCredit = !!caps?.["action:approve_credit_sale"]
  const [form, setForm] = useState({ party: "", paid_amount: "1000", mode_of_payment: "Cash" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({
        payment_type: "Receive",
        party_type: "Customer",
        party: form.party,
        paid_amount: parseFloat(form.paid_amount),
        mode_of_payment: form.mode_of_payment,
      } as any)
      toast.success("Payment recorded")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  const handleCreditApprove = async (name: string) => {
    try {
      await call.post("subamaz.api.admin.approve_credit_sale", { invoice: name })
      toast.success("Credit approved")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="payments-page">
      <h1 className="text-2xl font-bold">Payments</h1>

      <Card>
        <CardHeader><CardTitle>Record Payment — Cash / Bank / Mobile Money / Card</CardTitle></CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-4">
          <div><Label>Customer</Label><Input value={form.party} onChange={(e) => setForm({ ...form, party: e.target.value })} placeholder="Customer" data-testid="pay-customer" /></div>
          <div><Label>Amount</Label><Input value={form.paid_amount} onChange={(e) => setForm({ ...form, paid_amount: e.target.value })} data-testid="pay-amount" /></div>
          <div><Label>Mode</Label><Select value={form.mode_of_payment} onValueChange={(v) => setForm({ ...form, mode_of_payment: v })}><SelectTrigger data-testid="pay-mode"><SelectValue /></SelectTrigger><SelectContent>{["Cash", "Bank", "Mobile Money", "Card"].map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}</SelectContent></Select></div>
          <div className="flex items-end"><Button onClick={handleCreate} data-testid="create-payment">Record</Button></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>List</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Party</TableHead><TableHead>Amount</TableHead><TableHead>Mode</TableHead><TableHead>Type</TableHead><TableHead>Credit</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`pay-${r.name}`}>
                    <TableCell>{r.name}</TableCell><TableCell>{r.party}</TableCell><TableCell>{r.paid_amount}</TableCell><TableCell>{r.mode_of_payment}</TableCell><TableCell>{r.payment_type}</TableCell>
                    <TableCell>
                      {canCredit ? <Button size="sm" variant="outline" onClick={() => handleCreditApprove(r.name)} data-testid={`credit-${r.name}`}>Approve Credit</Button> : <Badge variant="outline">No capability</Badge>}
                    </TableCell>
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
