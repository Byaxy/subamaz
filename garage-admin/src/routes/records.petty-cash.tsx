import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { usePettyCash, useCreatePettyCash } from "@/lib/queries/money"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { toast } from "sonner"

export const Route = createFileRoute("/records/petty-cash")({
  component: PettyCashPage,
})

function PettyCashPage() {
  const { data, isLoading } = usePettyCash()
  const create = useCreatePettyCash()
  const { data: caps } = useMyCapabilities()
  const canRecord = !!caps?.["action:record_petty_cash"]
  const [form, setForm] = useState({ amount: "", description: "", expense_type: "Misc" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({ amount: parseFloat(form.amount), description: form.description, expense_type: form.expense_type })
      toast.success("Petty cash recorded")
      setForm({ amount: "", description: "", expense_type: "Misc" })
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="petty-cash-page">
      <h1 className="text-2xl font-bold">Petty Cash</h1>

      <Card>
        <CardHeader><CardTitle>Expense Log — gated by action:record_petty_cash</CardTitle></CardHeader>
        <CardContent className="flex flex-col gap-2">
          {!canRecord && <Badge variant="destructive">No capability — read only</Badge>}
          <div className="grid gap-2 md:grid-cols-3">
            <div><Label>Amount *</Label><Input value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="50000" data-testid="pc-amount" /></div>
            <div><Label>Expense Type</Label><Select value={form.expense_type} onValueChange={(v) => setForm({ ...form, expense_type: v })}><SelectTrigger data-testid="pc-type"><SelectValue /></SelectTrigger><SelectContent>{["Fuel", "Office", "Travel", "Misc", "Other"].map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
            <div className="flex items-end"><Button onClick={handleCreate} disabled={!canRecord || !form.amount || !form.description} data-testid="pc-create">Record</Button></div>
          </div>
          <div><Label>Description *</Label><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="pc-desc" /></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Log</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Date</TableHead><TableHead>Amount</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`pc-${r.name}`}>
                    <TableCell>{r.name}</TableCell><TableCell>{r.posting_date}</TableCell><TableCell>{r.amount}</TableCell><TableCell>{r.expense_type}</TableCell><TableCell><Badge>{r.status}</Badge></TableCell>
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
