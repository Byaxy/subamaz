import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useQuotation, useApproveQuotation } from "@/lib/queries/portal"
import { toast } from "sonner"

export const Route = createFileRoute("/quotation/$name")({
  component: QuotationPage,
})

function QuotationPage() {
  const { name } = Route.useParams()
  const { data, isLoading } = useQuotation(name)
  const approve = useApproveQuotation()

  const q: any = (data as any)?.message || data

  const handle = async (action: "Approve" | "Reject") => {
    try {
      await approve.mutateAsync({ name, action })
      toast.success(`${action}d`)
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  if (isLoading) return <Skeleton className="h-32" />

  return (
    <div className="space-y-4" data-testid="quotation-page">
      <h1 className="text-2xl font-bold">Quotation {name}</h1>
      <Card>
        <CardHeader><CardTitle>Customer: {q?.customer_name || q?.customer}</CardTitle></CardHeader>
        <CardContent>
          <div className="text-sm">Grand Total: {q?.grand_total}</div>
          <div className="text-sm">Status: {q?.status}</div>
          <div className="flex gap-2 mt-4">
            <Button onClick={() => handle("Approve")} data-testid="approve-quotation">Approve</Button>
            <Button variant="outline" onClick={() => handle("Reject")} data-testid="reject-quotation">Reject</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
