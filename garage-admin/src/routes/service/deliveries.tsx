import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useDeliveries, useCreateDelivery, useServiceOrders, useVehicles } from "@/lib/queries/service"
import { toast } from "sonner"
import { DocumentModal } from "@/components/common/DocumentModal"

export const Route = createFileRoute("/service/deliveries")({
  component: DeliveriesPage,
})

const CHECKLIST = ["Invoice Paid", "Customer Signed", "Vehicle Cleaned", "Accessories Returned", "Spare Keys Returned", "Old Parts Returned", "Photos Taken"] as const

function DeliveriesPage() {
  const { data, isLoading } = useDeliveries()
  const create = useCreateDelivery()
  const sos = useServiceOrders()
  const vehicles = useVehicles()
  const [form, setForm] = useState<any>({ service_order: "", vehicle: "", customer: "", checklist: [], photos: [] })
  const [docModal, setDocModal] = useState<{ open: boolean; name: string }>({ open: false, name: "" })

  const toggleCheck = (item: string, checked: boolean) => {
    const next = checked ? [...form.checklist, { checklist_item: item, completed: 1 }] : form.checklist.filter((c: any) => c.checklist_item !== item)
    setForm({ ...form, checklist: next })
  }

  const handleCreate = async () => {
    try {
      const res: any = await create.mutateAsync({
        service_order: form.service_order,
        vehicle: form.vehicle,
        customer: form.customer,
        checklist: form.checklist,
        photos: form.photos,
      } as any)
      // Try to submit
      const { db } = await import("@/lib/frappe-client")
      await db.updateDoc("Vehicle Delivery", res.name, { docstatus: 1 } as any)
      toast.success(`Delivery ${res.name}`)
      setDocModal({ open: true, name: res.name })
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="deliveries-page">
      <h1 className="text-2xl font-bold">Deliveries</h1>

      <Card>
        <CardHeader>
          <CardTitle>Create Delivery</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div>
            <Label>Service Order</Label>
            <select
              value={form.service_order}
              onChange={(e) => {
                const so = (sos.data || []).find((s: any) => s.name === e.target.value)
                setForm({ ...form, service_order: e.target.value, vehicle: so?.vehicle || "", customer: so?.customer || "" })
              }}
              className="w-full border rounded p-2"
              data-testid="delivery-so"
            >
              <option value="">Select SO</option>
              {(sos.data || []).map((s: any) => (
                <option key={s.name} value={s.name}>
                  {s.name} — {s.customer}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Vehicle</Label>
            <select value={form.vehicle} onChange={(e) => setForm({ ...form, vehicle: e.target.value })} className="w-full border rounded p-2" data-testid="delivery-vehicle">
              <option value="">Select vehicle</option>
              {(vehicles.data || []).map((v: any) => (
                <option key={v.name} value={v.name}>
                  {v.registration_number}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Checklist</Label>
            {CHECKLIST.map((c) => (
              <label key={c} className="flex items-center gap-2 text-sm">
                <Checkbox checked={!!form.checklist.find((x: any) => x.checklist_item === c)} onCheckedChange={(v) => toggleCheck(c, !!v)} data-testid={`delivery-${c}`} />
                {c}
              </label>
            ))}
          </div>
          <div>
            <Label>Photos (file)</Label>
            <Input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) setForm({ ...form, photos: [...form.photos, { photo: URL.createObjectURL(f), photo_type: "Front" }] })
              }}
              data-testid="delivery-photo"
            />
          </div>
          <Button onClick={handleCreate} data-testid="create-delivery">
            Create & Submit
          </Button>
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
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>SO</TableHead>
                  <TableHead>Receipt</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`delivery-${r.name}`}>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.vehicle}</TableCell>
                    <TableCell>{r.customer}</TableCell>
                    <TableCell>{r.service_order}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => setDocModal({ open: true, name: r.name })} data-testid={`receipt-${r.name}`}>
                        Receipt
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <DocumentModal open={docModal.open} onOpenChange={(open) => setDocModal({ ...docModal, open })} doctype="Vehicle Delivery" name={docModal.name} />
    </div>
  )
}
