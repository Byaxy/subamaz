import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useDepartments, useCreateDepartment, useUpdateDepartment } from "@/lib/queries/setup"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"

export const Route = createFileRoute("/setup/departments")({
  component: DepartmentsPage,
})

function DepartmentsPage() {
  const { data, isLoading } = useDepartments()
  const create = useCreateDepartment()
  const update = useUpdateDepartment()
  const { data: caps } = useMyCapabilities()
  const canEdit = !!caps?.["action:change_settings"]
  const [form, setForm] = useState({ department_name: "", default_hourly_rate: "" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({ department_name: form.department_name, default_hourly_rate: parseFloat(form.default_hourly_rate) || 0 } as any)
      toast.success("Created")
      setForm({ department_name: "", default_hourly_rate: "" })
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  const toggleActive = async (row: any) => {
    try {
      await update.mutateAsync({ name: row.name, data: { is_active: row.is_active ? 0 : 1 } as any })
      toast.success("Updated")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="departments-page">
      <h1 className="text-2xl font-bold">Departments</h1>
      {!canEdit && <Badge variant="destructive">Read only — action:change_settings required</Badge>}

      <Card>
        <CardHeader><CardTitle>Create Department</CardTitle></CardHeader>
        <CardContent className="flex gap-2">
          <div><Label>Name</Label><Input value={form.department_name} onChange={(e) => setForm({ ...form, department_name: e.target.value })} data-testid="dept-name" /></div>
          <div><Label>Hourly Rate</Label><Input type="number" value={form.default_hourly_rate} onChange={(e) => setForm({ ...form, default_hourly_rate: e.target.value })} data-testid="dept-rate" /></div>
          <div className="flex items-end"><Button onClick={handleCreate} disabled={!canEdit} data-testid="create-dept">Create</Button></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>List</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Rate</TableHead><TableHead>Active</TableHead><TableHead>Toggle</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`dept-${r.name}`}>
                    <TableCell>{r.department_name}</TableCell><TableCell>{r.default_hourly_rate}</TableCell><TableCell>{r.is_active ? "Yes" : "No"}</TableCell>
                    <TableCell><Button size="sm" variant="outline" onClick={() => toggleActive(r)} disabled={!canEdit} data-testid={`toggle-${r.name}`}>Toggle</Button></TableCell>
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
