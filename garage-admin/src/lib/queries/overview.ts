import { useQuery } from "@tanstack/react-query"
import { call } from "../frappe-client"

export const useOverviewStats = (from_date?: string, to_date?: string) =>
  useQuery({
    queryKey: ["overview", "stats", from_date, to_date],
    queryFn: () => call.get("subamaz.api.reports.get_overview_stats", { from_date, to_date }),
  })

export const useRevenueTrend = (from_date?: string, to_date?: string) =>
  useQuery({
    queryKey: ["overview", "trend", from_date, to_date],
    queryFn: () => call.get("subamaz.api.reports.get_revenue_trend", { from_date, to_date }),
  })

export const useMoneyInBreakdown = (from_date?: string, to_date?: string) =>
  useQuery({
    queryKey: ["overview", "money-in", from_date, to_date],
    queryFn: () => call.get("subamaz.api.reports.get_money_in_breakdown", { from_date, to_date }),
  })

export const useReceivablesAging = () =>
  useQuery({
    queryKey: ["overview", "aging"],
    queryFn: () => call.get("subamaz.api.reports.get_receivables_aging"),
  })
