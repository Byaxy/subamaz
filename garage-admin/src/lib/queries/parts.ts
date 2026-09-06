import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { call, db } from "../frappe-client"

export const useItems = (search?: string) =>
  useQuery({
    queryKey: ["parts", "items", search],
    queryFn: () =>
      db.getDocList("Item", {
        fields: ["name", "item_code", "item_name", "item_group", "stock_uom", "valuation_rate", "is_stock_item"],
        filters: search ? [["Item", "item_code", "like", `%${search}%`]] : undefined,
        limit: 50,
      }),
  })

export const useItem = (name: string) =>
  useQuery({
    queryKey: ["parts", "item", name],
    queryFn: () => db.getDoc("Item", name),
    enabled: !!name,
  })

export const useStockStatus = (warehouse?: string) =>
  useQuery({
    queryKey: ["parts", "stock-status", warehouse],
    queryFn: () => call.get("subamaz.api.admin.get_stock_status", { warehouse }),
  })

export const useWarehouses = () =>
  useQuery({
    queryKey: ["parts", "warehouses"],
    queryFn: () => db.getDocList("Warehouse", { fields: ["name", "warehouse_name", "is_group", "company"], limit: 50 }),
  })

export const useStockTransfers = () =>
  useQuery({
    queryKey: ["parts", "transfers"],
    queryFn: () =>
      db.getDocList("Stock Entry", {
        fields: ["name", "posting_date", "stock_entry_type", "purpose", "from_warehouse", "to_warehouse"],
        filters: [["Stock Entry", "purpose", "=", "Material Transfer"]],
        limit: 50,
      }),
  })

export const useCreateTransfer = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Stock Entry", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["parts", "transfers"] }),
  })
}

export const useRestockPreview = (warehouse?: string) =>
  useQuery({
    queryKey: ["parts", "restock-preview", warehouse],
    queryFn: () => call.get("subamaz.api.admin.get_restock_preview", { warehouse }),
  })

export const useCreatePurchaseOrder = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Purchase Order", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["parts", "restock-preview"] }),
  })
}
