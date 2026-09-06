import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useStockTransfers, useCreateTransfer, useWarehouses, useItems } from "@/lib/queries/parts"
import { toast } from "sonner"

export const Route = createFileRoute("/parts/transfers")({
  component: TransfersPage,
})

function TransfersPage() {
  const { data, isLoading } = useStockTransfers()
  const create = useCreateTransfer()
  const warehouses = useWarehouses()
  const items = useItems()
  const [form, setForm] = useState({ item_code: "", qty: "1", from_warehouse: "", to_warehouse: "" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({
        stock_entry_type: "Material Transfer",
        purpose: "Material Transfer",
        from_warehouse: form.from_warehouse,
        to_warehouse: form.to_warehouse,
        items: [{ item_code: form.item_code, qty: parseFloat(form.qty), s_warehouse: form.from_warehouse, t_warehouse: form.to_warehouse }] as any,
      } as any)
      toast.success("Transfer created")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="transfers-page">
      <h1 className="text-2xl font-bold">Stock Transfers</h1>

      <Card>
        <CardHeader>
          <CardTitle>Create Transfer</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-4">
          <div>
            <Label>Item</Label>
            <select value={form.item_code} onChange={(e) => setForm({ ...form, item_code: e.target.value })} className="w-full border rounded p-2" data-testid="transfer-item">
              <option value="">Select</option>
              {(items.data || []).map((it: any) => (
                <option key={it.item_code} value={it.item_code}>
                  {it.item_code}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Qty</Label>
            <Input value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} data-testid="transfer-qty" />
          </div>
          <div>
            <Label>From</Label>
            <select value={form.from_warehouse} onChange={(e) => setForm({ ...form, from_warehouse: e.target.value })} className="w-full border rounded p-2" data-testid="transfer-from">
              <option value="">Select</option>
              {(warehouses.data || []).map((w: any) => (
                <option key={w.name} value={w.name}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>To</Label>
            <select value={form.to_warehouse} onChange={(e) => setForm({ ...form, to_warehouse: e.target.value })} className="w-full border rounded p-2" data-testid="transfer-to">
              <option value="">Select</option>
              {(warehouses.data || []).map((w: any) => (
                <option key={w.name} value={w.name}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-4">
            <Button onClick={handleCreate} data-testid="create-transfer">
              Create Transfer
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>List</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`transfer-${r.name}`}>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.posting_date}</TableCell>
                    <TableCell>{r.from_warehouse}</TableCell>
                    <TableCell>{r.to_warehouse}</TableCell>
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
