import { createFileRoute, Link } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useVehicles, useCreateVehicle, useCustomers } from "@/lib/queries/customers"
import { toast } from "sonner"
import { DocumentModal } from "@/components/common/DocumentModal"

export const Route = createFileRoute("/vehicles")({
  component: VehiclesPage,
})

function VehiclesPage() {
  const [search, setSearch] = useState("")
  const { data, isLoading } = useVehicles(search)
  const create = useCreateVehicle()
  const customers = useCustomers()
  const [form, setForm] = useState({ registration_number: "", vin: "", customer: "", make: "", model: "" })
  const [docModal, setDocModal] = useState<{ open: boolean; name: string }>({ open: false, name: "" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({
        registration_number: form.registration_number,
        vin: form.vin,
        customer: form.customer,
        make: form.make,
        model: form.model,
      } as any)
      toast.success("Vehicle created")
      setForm({ registration_number: "", vin: "", customer: "", make: "", model: "" })
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="vehicles-page">
      <h1 className="text-2xl font-bold">Vehicles</h1>

      <Card>
        <CardHeader>
          <CardTitle>Create / Register Vehicle</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-3">
          <div>
            <Label>Registration *</Label>
            <Input value={form.registration_number} onChange={(e) => setForm({ ...form, registration_number: e.target.value })} data-testid="veh-reg" />
          </div>
          <div>
            <Label>VIN</Label>
            <Input value={form.vin} onChange={(e) => setForm({ ...form, vin: e.target.value })} data-testid="veh-vin" />
          </div>
          <div>
            <Label>Customer *</Label>
            <select value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })} className="w-full border rounded p-2" data-testid="veh-customer">
              <option value="">Select</option>
              {(customers.data || []).map((c: any) => (
                <option key={c.name} value={c.name}>
                  {c.customer_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Make</Label>
            <Input value={form.make} onChange={(e) => setForm({ ...form, make: e.target.value })} />
          </div>
          <div>
            <Label>Model</Label>
            <Input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
          </div>
          <div className="flex items-end">
            <Button onClick={handleCreate} data-testid="create-vehicle">
              Create
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>List</CardTitle>
          <div className="flex gap-2">
            <Input placeholder="Search registration/VIN" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="vehicle-search" />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Registration</TableHead>
                  <TableHead>VIN</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>History</TableHead>
                  <TableHead>Print</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((v: any) => (
                  <TableRow key={v.name} data-testid={`vehicle-${v.name}`}>
                    <TableCell className="font-medium">{v.registration_number}</TableCell>
                    <TableCell>{v.vin}</TableCell>
                    <TableCell>{v.customer}</TableCell>
                    <TableCell>
                      <Badge>{v.current_status}</Badge>
                    </TableCell>
                    <TableCell>
                      <Button asChild size="sm" variant="outline">
                        <Link to="/vehicles/$vehicleId/history" params={{ vehicleId: v.name }} data-testid={`history-${v.name}`}>
                          History
                        </Link>
                      </Button>
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={() => setDocModal({ open: true, name: v.name })} data-testid={`print-${v.name}`}>
                        Doc
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <DocumentModal open={docModal.open} onOpenChange={(open) => setDocModal({ ...docModal, open })} doctype="Garage Vehicle" name={docModal.name} />
    </div>
  )
}
