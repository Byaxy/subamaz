import { createFileRoute, Link } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useReceptions } from "@/lib/queries/service"

export const Route = createFileRoute("/service/receptions")({
  component: ReceptionsPage,
})

function ReceptionsPage() {
  const { data, isLoading } = useReceptions("Submitted")

  return (
    <div className="space-y-4" data-testid="receptions-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Receptions</h1>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/service/receptions/queue" data-testid="go-queue">
              Queue
            </Link>
          </Button>
          <Button asChild>
            <Link to="/service/reception/new" data-testid="new-reception">
              New Reception
            </Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Submitted receptions</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`reception-row-${r.name}`}>
                    <TableCell className="font-medium">{r.name}</TableCell>
                    <TableCell>{r.customer}</TableCell>
                    <TableCell>{r.vehicle}</TableCell>
                    <TableCell>{r.status}</TableCell>
                    <TableCell>{r.reception_date}</TableCell>
                  </TableRow>
                ))}
                {(!data || data.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                      No receptions
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
