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
import { useInspections, useCreateInspection, useVehicles, useEmployees } from "@/lib/queries/service"
import { toast } from "sonner"

export const Route = createFileRoute("/service/inspections")({
  component: InspectionsPage,
})

const SECTIONS = ["Engine", "Transmission", "Suspension", "Electrical", "Interior", "Exterior", "Brakes"] as const
const RESULTS = ["Pass", "Fail", "Advisory", "Not Checked"] as const

function InspectionsPage() {
  const { data, isLoading } = useInspections()
  const create = useCreateInspection()
  const vehicles = useVehicles()
  const employees = useEmployees()
  const [form, setForm] = useState<any>({
    vehicle: "",
    inspector: "",
    inspection_type: "Routine",
    mileage: "",
    inspection_result: "Good",
    recommendation: "Safe to Drive",
    notes: "",
    checklist: [],
  })
  const [item, setItem] = useState({ section: "Engine", checklist_item: "", result: "Pass", notes: "" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({
        vehicle: form.vehicle,
        inspector: form.inspector,
        inspection_type: form.inspection_type,
        mileage: form.mileage ? parseInt(form.mileage) : undefined,
        inspection_result: form.inspection_result,
        recommendation: form.recommendation,
        notes: form.notes,
        checklist: form.checklist,
      } as any)
      toast.success("Inspection created")
      setForm({ vehicle: "", inspector: "", inspection_type: "Routine", mileage: "", inspection_result: "Good", recommendation: "Safe to Drive", notes: "", checklist: [] })
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="inspections-page">
      <h1 className="text-2xl font-bold">Inspections</h1>

      <Card>
        <CardHeader>
          <CardTitle>Create Inspection</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Vehicle</Label>
              <Select value={form.vehicle} onValueChange={(v) => setForm({ ...form, vehicle: v })}>
                <SelectTrigger data-testid="insp-vehicle">
                  <SelectValue placeholder="Select vehicle" />
                </SelectTrigger>
                <SelectContent>
                  {(vehicles.data || []).map((v: any) => (
                    <SelectItem key={v.name} value={v.name}>
                      {v.registration_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Inspector</Label>
              <Select value={form.inspector} onValueChange={(v) => setForm({ ...form, inspector: v })}>
                <SelectTrigger data-testid="insp-inspector">
                  <SelectValue placeholder="Select inspector" />
                </SelectTrigger>
                <SelectContent>
                  {(employees.data || []).map((e: any) => (
                    <SelectItem key={e.name} value={e.name}>
                      {e.employee_name || e.first_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Type</Label>
              <Select value={form.inspection_type} onValueChange={(v) => setForm({ ...form, inspection_type: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["Pre-Purchase", "Routine", "Insurance", "Repair Diagnosis", "Warranty", "Annual"].map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Mileage</Label>
              <Input value={form.mileage} onChange={(e) => setForm({ ...form, mileage: e.target.value })} data-testid="insp-mileage" />
            </div>
          </div>
          <div>
            <Label>Notes</Label>
            <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </div>

          <div className="border p-2 rounded flex flex-col gap-2">
            <h4 className="font-medium text-sm">Checklist</h4>
            <div className="grid grid-cols-4 gap-2">
              <Select value={item.section} onValueChange={(v) => setItem({ ...item, section: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SECTIONS.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input placeholder="Item" value={item.checklist_item} onChange={(e) => setItem({ ...item, checklist_item: e.target.value })} data-testid="insp-item" />
              <Select value={item.result} onValueChange={(v) => setItem({ ...item, result: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RESULTS.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={() => {
                  setForm({ ...form, checklist: [...form.checklist, item] })
                  setItem({ section: "Engine", checklist_item: "", result: "Pass", notes: "" })
                }}
                data-testid="add-checklist"
              >
                Add
              </Button>
            </div>
            <div data-testid="checklist-count">Items: {form.checklist.length}</div>
          </div>

          <Button onClick={handleCreate} data-testid="create-inspection">
            Create
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
                  <TableHead>Inspector</TableHead>
                  <TableHead>Result</TableHead>
                  <TableHead>Recommendation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`inspection-${r.name}`}>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.vehicle}</TableCell>
                    <TableCell>{r.inspector}</TableCell>
                    <TableCell>{r.inspection_result}</TableCell>
                    <TableCell>{r.recommendation}</TableCell>
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
