import { createFileRoute, Link } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useEmployees } from "@/lib/queries/staff"
import { useMyCapabilities } from "@/lib/queries/capabilities"

export const Route = createFileRoute("/staff/technicians")({
  component: TechniciansPage,
})

function TechniciansPage() {
  const { data, isLoading } = useEmployees()
  const { data: caps } = useMyCapabilities()
  const canViewAll = !!caps?.["action:view_all_technician_performance"]

  return (
    <div className="space-y-4" data-testid="technicians-page">
      <h1 className="text-2xl font-bold">Technicians</h1>
      <p className="text-muted-foreground">Employee list — {canViewAll ? "all performance visible" : "own performance only"}</p>

      <Card>
        <CardHeader><CardTitle>Employees</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Employee Name</TableHead><TableHead>Department</TableHead><TableHead>Status</TableHead><TableHead>Performance</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((e: any) => (
                  <TableRow key={e.name} data-testid={`tech-${e.name}`}>
                    <TableCell>{e.name}</TableCell><TableCell>{e.employee_name || e.first_name}</TableCell><TableCell>{e.department}</TableCell><TableCell><Badge>{e.status}</Badge></TableCell>
                    <TableCell>
                      {canViewAll ? <Button size="sm" variant="outline" asChild><Link to="/insights/reports">View</Link></Button> : <span className="text-xs text-muted-foreground">Own only</span>}
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
