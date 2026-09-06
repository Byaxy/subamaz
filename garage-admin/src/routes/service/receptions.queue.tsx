import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useReceptionQueue, useUpdateReception } from "@/lib/queries/service"
import { useNavigate } from "@tanstack/react-router"
import { toast } from "sonner"

export const Route = createFileRoute("/service/receptions/queue")({
  component: QueuePage,
})

function QueuePage() {
  const { data, isLoading } = useReceptionQueue()
  const update = useUpdateReception()
  const navigate = useNavigate()

  const handleResume = (name: string) => {
    navigate({ to: "/service/reception/new", search: { resume: name } as any })
  }

  const handleCancel = async (name: string) => {
    try {
      await update.mutateAsync({ name, data: { status: "Cancelled" } } as any)
      toast.success("Cancelled")
    } catch {
      toast.error("Cancel failed")
    }
  }

  return (
    <div className="space-y-4" data-testid="queue-page">
      <h1 className="text-2xl font-bold">Parked Queue</h1>
      <p className="text-muted-foreground">Incomplete receptions — Draft — Parked</p>

      <Card>
        <CardHeader>
          <CardTitle>Queue</CardTitle>
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
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`queue-row-${r.name}`}>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.customer}</TableCell>
                    <TableCell>{r.vehicle}</TableCell>
                    <TableCell className="flex gap-2">
                      <Button size="sm" onClick={() => handleResume(r.name)} data-testid={`resume-${r.name}`}>
                        Resume
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleCancel(r.name)} data-testid={`cancel-${r.name}`}>
                        Cancel
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data || data.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">
                      Queue empty
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
