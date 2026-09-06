import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/invoices/$name/pay")({
  component: PayPage,
})

function PayPage() {
  const { name } = Route.useParams()

  return (
    <div className="space-y-4" data-testid="pay-page">
      <h1 className="text-2xl font-bold">Pay Invoice {name}</h1>
      <Card>
        <CardHeader><CardTitle>Payment</CardTitle><CardDescription>Online payment gateway to be configured</CardDescription></CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">This is a stub. Configure a payment gateway to enable online payments.</div>
          <Button className="mt-4" disabled data-testid="pay-button">Pay Now (coming soon)</Button>
        </CardContent>
      </Card>
    </div>
  )
}
