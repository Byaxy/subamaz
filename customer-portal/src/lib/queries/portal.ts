import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { call } from "../frappe-client"

export const useMyVehicles = () =>
  useQuery({
    queryKey: ["portal", "vehicles"],
    queryFn: () => call.get("subamaz.api.portal.get_my_vehicles"),
  })

export const useVehicleDetail = (vehicle: string) =>
  useQuery({
    queryKey: ["portal", "vehicle", vehicle],
    queryFn: () => call.get("subamaz.api.portal.get_vehicle_detail", { vehicle }),
    enabled: !!vehicle,
  })

export const useServiceOrderProgress = (name: string) =>
  useQuery({
    queryKey: ["portal", "service-order", name],
    queryFn: () => call.get("subamaz.api.portal.get_service_order_progress", { name }),
    enabled: !!name,
  })

export const useCustomerTimeline = (service_order?: string) =>
  useQuery({
    queryKey: ["portal", "timeline", service_order],
    queryFn: () => call.get("subamaz.api.portal.get_customer_timeline", { service_order }),
    enabled: !!service_order,
  })

export const useQuotation = (name: string) =>
  useQuery({
    queryKey: ["portal", "quotation", name],
    queryFn: () => call.get("subamaz.api.portal.get_quotation", { name }),
    enabled: !!name,
  })

export const useApproveQuotation = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, action }: { name: string; action: "Approve" | "Reject" }) =>
      call.post("subamaz.api.portal.approve_quotation", { name, action }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portal", "quotation"] }),
  })
}

export const useMyInvoices = () =>
  useQuery({
    queryKey: ["portal", "invoices"],
    queryFn: () => call.get("subamaz.api.portal.get_my_invoices"),
  })

export const useServiceHistory = () =>
  useQuery({
    queryKey: ["portal", "history"],
    queryFn: () => call.get("subamaz.api.portal.get_service_history"),
  })

export const useReceptionRecord = (name: string) =>
  useQuery({
    queryKey: ["portal", "reception", name],
    queryFn: () => call.get("subamaz.api.portal.get_reception_record", { name }),
    enabled: !!name,
  })
