import { createFileRoute, Link } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useServiceCounts } from "@/lib/queries/service"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = createFileRoute("/service/guide")({
  component: GuidePage,
})

const steps = [
  { n: 1, title: "Vehicle Reception", desc: "Check-in, damage markers, photos, accessories, terms + signatures", to: "/service/reception/new", key: "receptions" },
  { n: 2, title: "Vehicle Inspection", desc: "Checklist by section, result + recommendation, PDF + email", to: "/service/inspections", key: "inspections" },
  { n: 3, title: "Service Order", desc: "Contract, diagnosis, workflow, auto-Project/Quotation, roll-ups", to: "/service/orders", key: "orders" },
  { n: 4, title: "Job Card", desc: "Workshop execution, time logs, parts, stock consumption, status chain", to: "/service/job-cards", key: "jobs" },
  { n: 5, title: "Quality Check", desc: "QA checklist, Pass/Fail gating, Ready QA → Completed", to: "/service/quality-checks", key: "qa" },
  { n: 6, title: "Vehicle Delivery", desc: "Checklist, photos, signatures, invoice, reminder + survey", to: "/service/deliveries", key: "deliveries" },
]

function GuidePage() {
  const counts = useServiceCounts()

  return (
    <div className="space-y-6" data-testid="guide-page">
      <div>
        <h1 className="text-2xl font-bold">Service Guide</h1>
        <p className="text-muted-foreground">Complete lifecycle — never used the app before? Start here.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {steps.map((s) => (
          <Card key={s.n} data-testid={`guide-step-${s.n}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <span className="size-7 rounded-full bg-[var(--app-primary)] text-white flex items-center justify-center text-sm font-bold">
                  {s.n}
                </span>
                <CardTitle className="text-base">{s.title}</CardTitle>
              </div>
              <CardDescription>{s.desc}</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <Badge variant="secondary">
                {counts.isLoading ? <Skeleton className="h-3 w-8" /> : (counts.data as any)?.[s.key] ?? 0} records
              </Badge>
              <Button asChild size="sm" variant="outline">
                <Link to={s.to} data-testid={`guide-open-${s.n}`}>
                  Open →
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Faster ways in</CardTitle>
          <CardDescription>Quick actions for power users</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button asChild>
            <Link to="/service/reception/new">Quick Reception</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/service/receptions/queue">Parked Queue</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/service/job-cards">Kanban Board</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
