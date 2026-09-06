import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { call, db } from "../frappe-client"

export const useProcurementCounts = () =>
  useQuery({
    queryKey: ["procurement", "counts"],
    queryFn: () => call.get("subamaz.api.admin.get_procurement_counts"),
  })

export const useSupplierQuotations = () =>
  useQuery({
    queryKey: ["procurement", "supplier-quotations"],
    queryFn: () => db.getDocList("Supplier Quotation", { fields: ["name", "supplier", "status", "transaction_date", "grand_total"], limit: 50 }),
  })

export const usePurchaseOrders = () =>
  useQuery({
    queryKey: ["procurement", "purchase-orders"],
    queryFn: () => db.getDocList("Purchase Order", { fields: ["name", "supplier", "status", "transaction_date", "grand_total"], limit: 50 }),
  })

export const usePurchaseInvoices = () =>
  useQuery({
    queryKey: ["procurement", "purchase-invoices"],
    queryFn: () => db.getDocList("Purchase Invoice", { fields: ["name", "supplier", "status", "posting_date", "grand_total"], limit: 50 }),
  })

export const usePurchaseReceipts = () =>
  useQuery({
    queryKey: ["procurement", "purchase-receipts"],
    queryFn: () => db.getDocList("Purchase Receipt", { fields: ["name", "supplier", "status", "posting_date"], limit: 50 }),
  })

export const useCreateSupplierQuotation = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Supplier Quotation", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["procurement", "supplier-quotations"] }),
  })
}

export const useCreatePurchaseOrder = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Purchase Order", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["procurement", "purchase-orders"] }),
  })
}

export const useCreatePurchaseInvoice = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Purchase Invoice", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["procurement", "purchase-invoices"] }),
  })
}
