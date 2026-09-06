import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { useUsers, useUserRoles, useUpdateUserRoles } from "@/lib/queries/staff"
import { useState } from "react"
import { toast } from "sonner"

export const Route = createFileRoute("/staff/roles")({
  component: RolesPage,
})

const GARAGE_ROLES = ["Garage Reception", "Garage Technician", "Garage Inspector", "Garage Supervisor", "Garage Service Advisor", "Garage Manager", "Garage Accountant"]

function RolesPage() {
  const { data, isLoading } = useUsers()
  const [selected, setSelected] = useState<string>("")
  const userRoles = useUserRoles(selected)
  const update = useUpdateUserRoles()
  const [role, setRole] = useState("")

  const handleAdd = async () => {
    if (!selected || !role) return
    const current = (userRoles.data as any)?.roles?.map((r: any) => r.role) || []
    if (current.includes(role)) {
      toast.error("Already has role")
      return
    }
    try {
      await update.mutateAsync({ user: selected, roles: [...current, role] })
      toast.success("Role added")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="roles-page">
      <h1 className="text-2xl font-bold">Roles</h1>
      <p className="text-muted-foreground">Manage garage role assignment to Users</p>

      <Card>
        <CardHeader><CardTitle>Users</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>User</TableHead><TableHead>Full Name</TableHead><TableHead>Type</TableHead><TableHead>Select</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((u: any) => (
                  <TableRow key={u.name} data-testid={`user-${u.name}`}>
                    <TableCell>{u.name}</TableCell><TableCell>{u.full_name}</TableCell><TableCell>{u.user_type}</TableCell>
                    <TableCell><Button size="sm" variant="outline" onClick={() => setSelected(u.name)} data-testid={`select-${u.name}`}>Manage</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selected && (
        <Card data-testid="role-manage">
          <CardHeader><CardTitle>Manage {selected}</CardTitle></CardHeader>
          <CardContent className="flex flex-col gap-2">
            <div>Current: {(userRoles.data as any)?.roles?.map((r: any) => r.role).join(", ") || "—"}</div>
            <div className="flex gap-2">
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger className="w-64" data-testid="role-select"><SelectValue placeholder="Select role" /></SelectTrigger>
                <SelectContent>
                  {GARAGE_ROLES.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                </SelectContent>
              </Select>
              <Button onClick={handleAdd} data-testid="add-role">Add Role</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
