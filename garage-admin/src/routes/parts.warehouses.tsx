import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useWarehouses } from "@/lib/queries/parts"

export const Route = createFileRoute("/parts/warehouses")({
  component: WarehousesPage,
})

function WarehousesPage() {
  const { data, isLoading } = useWarehouses()

  return (
    <div className="space-y-4" data-testid="warehouses-page">
      <h1 className="text-2xl font-bold">Warehouses</h1>

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
                  <TableHead>Warehouse Name</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Group</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((w: any) => (
                  <TableRow key={w.name} data-testid={`wh-${w.name}`}>
                    <TableCell>{w.name}</TableCell>
                    <TableCell>{w.warehouse_name}</TableCell>
                    <TableCell>{w.company}</TableCell>
                    <TableCell>
                      <Badge variant={w.is_group ? "secondary" : "outline"}>{w.is_group ? "Group" : "Leaf"}</Badge>
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
