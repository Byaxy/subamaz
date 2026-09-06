import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { call, db } from "../frappe-client"

export const useMoneyCounts = () =>
  useQuery({
    queryKey: ["money", "counts"],
    queryFn: () => call.get("subamaz.api.admin.get_money_counts"),
  })

export const useInvoices = () =>
  useQuery({
    queryKey: ["money", "invoices"],
    queryFn: () => db.getDocList("Sales Invoice", { fields: ["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"], limit: 50 }),
  })

export const usePayments = () =>
  useQuery({
    queryKey: ["money", "payments"],
    queryFn: () => db.getDocList("Payment Entry", { fields: ["name", "party", "posting_date", "paid_amount", "mode_of_payment", "payment_type", "status"], limit: 50 }),
  })

export const useQuotations = () =>
  useQuery({
    queryKey: ["money", "quotations"],
    queryFn: () => db.getDocList("Quotation", { fields: ["name", "customer_name", "status", "transaction_date", "grand_total"], limit: 50 }),
  })

export const usePettyCash = () =>
  useQuery({
    queryKey: ["money", "petty-cash"],
    queryFn: () => db.getDocList("Petty Cash Log", { fields: ["name", "posting_date", "amount", "description", "expense_type", "status"], limit: 50 }),
  })

export const useCreatePayment = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Payment Entry", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["money", "payments"] }),
  })
}

export const useApplyDiscount = () =>
  useMutation({
    mutationFn: ({ invoice, discount_amount }: { invoice: string; discount_amount: number }) =>
      call.post("subamaz.api.admin.apply_invoice_discount", { invoice, discount_amount: discount_amount.toString() }),
  })

export const useVoidInvoice = () =>
  useMutation({
    mutationFn: (invoice: string) => call.post("subamaz.api.admin.void_invoice", { invoice }),
  })

export const useApproveCreditSale = () =>
  useMutation({
    mutationFn: (invoice: string) => call.post("subamaz.api.admin.approve_credit_sale", { invoice }),
  })

export const useCreatePettyCash = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { amount: number; description: string; expense_type?: string }) =>
      call.post("subamaz.api.admin.create_petty_cash", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["money", "petty-cash"] }),
  })
}

export const useCustomerStatement = (customer?: string, filters?: Record<string, unknown>) =>
  useQuery({
    queryKey: ["money", "statement", customer, filters],
    queryFn: () => call.post("subamaz.api.reports.run_report", { report_name: "Customer Statement Summary", filters: { customer, ...filters } } as any),
    enabled: !!customer,
  })
