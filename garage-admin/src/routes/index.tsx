import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useOverviewStats, useRevenueTrend, useMoneyInBreakdown, useReceivablesAging } from "@/lib/queries/overview"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"
import { DocumentModal } from "@/components/common/DocumentModal"

export const Route = createFileRoute("/")({
  component: OverviewPage,
})

export function OverviewPage() {
  const stats = useOverviewStats()
  const trend = useRevenueTrend()
  const money = useMoneyInBreakdown()
  const aging = useReceivablesAging()
  const [docModal, setDocModal] = useState<{ open: boolean; doctype: string; name: string }>({ open: false, doctype: "", name: "" })

  if (stats.isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-4">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    )
  }

  if (stats.isError) {
    return <div className="text-sm text-destructive">Failed to load overview: {(stats.error as Error).message}</div>
  }

  const s = stats.data as any

  return (
    <div className="space-y-6" data-testid="overview-page">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--app-page-head-text)" }}>
          Overview
        </h1>
        <p className="text-muted-foreground">Garage performance at a glance</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card data-testid="stat-jobs">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Jobs Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{s.jobs_completed}</div>
            <Badge variant={s.jobs_completed_change_pct >= 0 ? "secondary" : "destructive"} className="mt-1">
              {s.jobs_completed_change_pct >= 0 ? "+" : ""}
              {s.jobs_completed_change_pct}% vs prev
            </Badge>
            <div className="text-xs text-muted-foreground mt-1">Prev: {s.jobs_completed_prev}</div>
          </CardContent>
        </Card>

        <Card data-testid="stat-revenue">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${Number(s.revenue_total).toLocaleString()}</div>
            <Badge variant={s.revenue_change_pct >= 0 ? "secondary" : "destructive"} className="mt-1">
              {s.revenue_change_pct >= 0 ? "+" : ""}
              {s.revenue_change_pct}% vs prev
            </Badge>
            <div className="text-xs text-muted-foreground mt-1">Margin {s.gross_margin_pct}%</div>
          </CardContent>
        </Card>

        <Card data-testid="stat-active">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Job Cards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{s.active_job_cards}</div>
            <div className="text-xs text-muted-foreground">In workshop</div>
          </CardContent>
        </Card>

        <Card data-testid="stat-outstanding">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Outstanding Invoices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${Number(s.outstanding_invoices_total).toLocaleString()}</div>
            <div className="text-xs text-muted-foreground">{s.outstanding_invoices_count} unpaid</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Revenue Trend</CardTitle>
          </CardHeader>
          <CardContent>
            {trend.isLoading ? (
              <Skeleton className="h-40" />
            ) : (
              <div className="space-y-1" data-testid="revenue-trend">
                {(trend.data?.series || []).map((row: any) => (
                  <div key={row.period} className="flex justify-between text-sm border-b py-1">
                    <span>{row.period}</span>
                    <span className="font-medium">${Number(row.revenue).toLocaleString()}</span>
                  </div>
                ))}
                {(!trend.data?.series || trend.data.series.length === 0) && <div className="text-sm text-muted-foreground">No data</div>}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Money In</CardTitle>
          </CardHeader>
          <CardContent>
            {money.isLoading ? (
              <Skeleton className="h-40" />
            ) : (
              <div className="space-y-1" data-testid="money-in">
                {(money.data?.breakdown || []).map((row: any) => (
                  <div key={row.mode} className="flex justify-between text-sm border-b py-1">
                    <span>{row.mode}</span>
                    <span className="font-medium">${Number(row.total).toLocaleString()}</span>
                  </div>
                ))}
                {(!money.data?.breakdown || money.data.breakdown.length === 0) && <div className="text-sm text-muted-foreground">No payments</div>}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Receivables Aging</CardTitle>
        </CardHeader>
        <CardContent>
          {aging.isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <div className="space-y-2" data-testid="aging">
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="rounded bg-muted p-3">
                  <div className="text-muted-foreground">Current (0-30)</div>
                  <div className="text-lg font-bold">${Number(aging.data?.buckets?.current_0_30 || 0).toLocaleString()}</div>
                </div>
                <div className="rounded bg-muted p-3">
                  <div className="text-muted-foreground">31-60</div>
                  <div className="text-lg font-bold">${Number(aging.data?.buckets?.over_30_60 || 0).toLocaleString()}</div>
                </div>
                <div className="rounded bg-muted p-3">
                  <div className="text-muted-foreground">Overdue 60+</div>
                  <div className="text-lg font-bold">${Number(aging.data?.buckets?.overdue_60_plus || 0).toLocaleString()}</div>
                </div>
              </div>
              <div className="pt-2">
                <h4 className="font-medium text-sm mb-1">Top Outstanding Customers</h4>
                {(aging.data?.top_customers || []).map((c: any) => (
                  <div key={c.customer} className="flex justify-between text-sm py-1 border-b">
                    <span>{c.customer}</span>
                    <span>${Number(c.outstanding).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <DocumentModal
        open={docModal.open}
        onOpenChange={(open) => setDocModal({ ...docModal, open })}
        doctype={docModal.doctype}
        name={docModal.name}
      />
    </div>
  )
}
