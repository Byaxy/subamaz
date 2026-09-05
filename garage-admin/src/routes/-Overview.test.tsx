import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { OverviewPage } from "./index"

vi.mock("@/lib/queries/overview", () => ({
  useOverviewStats: () => ({
    data: {
      jobs_completed: 5,
      jobs_completed_prev: 3,
      jobs_completed_change_pct: 66.67,
      revenue_total: 100000,
      revenue_prev_total: 80000,
      revenue_change_pct: 25,
      gross_margin_pct: 20,
      active_job_cards: 3,
      outstanding_invoices_total: 50000,
      outstanding_invoices_count: 2,
    },
    isLoading: false,
    isError: false,
  }),
  useRevenueTrend: () => ({
    data: { series: [{ period: "2026-08", revenue: 50000 }] },
    isLoading: false,
  }),
  useMoneyInBreakdown: () => ({
    data: { breakdown: [{ mode: "Cash", total: 20000 }] },
    isLoading: false,
  }),
  useReceivablesAging: () => ({
    data: { buckets: { current_0_30: 1000, over_30_60: 2000, overdue_60_plus: 3000 }, top_customers: [] },
    isLoading: false,
  }),
}))

describe("Overview", () => {
  it("renders mock overview data", async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <OverviewPage />
      </QueryClientProvider>
    )

    expect(await screen.findByTestId("overview-page")).toBeInTheDocument()
    expect(screen.getByTestId("stat-jobs")).toBeInTheDocument()
    expect(screen.getByText("5")).toBeInTheDocument()
    expect(screen.getByText("$100,000")).toBeInTheDocument()
  })
})
