import { createFileRoute, Link } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useProcurementCounts } from "@/lib/queries/procurement"

export const Route = createFileRoute("/procurement/guide")({
  component: ProcurementGuide,
})

const steps = [
  { n: 1, title: "Supplier Quotation", desc: "Request prices from suppliers", to: "/procurement/supplier-quotations", key: "supplier_quotations" },
  { n: 2, title: "Purchase Order", desc: "Order from chosen supplier", to: "/procurement/purchase-orders", key: "purchase_orders" },
  { n: 3, title: "Purchase Invoice", desc: "Bill from supplier", to: "/procurement/purchase-invoices", key: "purchase_invoices" },
  { n: 4, title: "Purchase Receipt", desc: "Goods received, stock updated", to: "/procurement/purchase-receipts", key: "purchase_receipts" },
]

export function ProcurementGuide() {
  const { data, isLoading } = useProcurementCounts()

  return (
    <div className="space-y-6" data-testid="procurement-guide">
      <div>
        <h1 className="text-2xl font-bold">Procurement Guide</h1>
        <p className="text-muted-foreground">From quotation to receipt</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {steps.map((s) => (
          <Card key={s.n} data-testid={`proc-guide-${s.n}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <span className="size-7 rounded-full bg-[var(--app-primary)] text-white flex items-center justify-center text-sm font-bold">{s.n}</span>
                <CardTitle className="text-base">{s.title}</CardTitle>
              </div>
              <CardDescription>{s.desc}</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <Badge variant="secondary">
                {isLoading ? <Skeleton className="h-3 w-8" /> : (data as any)?.[s.key] ?? 0} records
              </Badge>
              <Button asChild size="sm" variant="outline">
                <Link to={s.to} data-testid={`proc-open-${s.n}`}>Open →</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Faster ways in</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Button asChild><Link to="/parts/restock">Restock</Link></Button>
          <Button asChild variant="outline"><Link to="/procurement/purchase-orders">Quick Receiving</Link></Button>
        </CardContent>
      </Card>
    </div>
  )
}
