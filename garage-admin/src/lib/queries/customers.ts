import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { call, db } from "../frappe-client"

export const useCustomers = (search?: string) =>
  useQuery({
    queryKey: ["customers", search],
    queryFn: () =>
      db.getDocList("Customer", {
        fields: ["name", "customer_name", "customer_type", "customer_group", "territory"],
        filters: search ? [["Customer", "customer_name", "like", `%${search}%`]] : undefined,
        limit: 50,
      }),
  })

export const useCustomer = (name: string) =>
  useQuery({
    queryKey: ["customer", name],
    queryFn: () => db.getDoc("Customer", name),
    enabled: !!name,
  })

export const useCreateCustomer = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Customer", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["customers"] }),
  })
}

export const useVehicles = (search?: string) =>
  useQuery({
    queryKey: ["garage-vehicles", search],
    queryFn: () =>
      db.getDocList("Garage Vehicle", {
        fields: ["name", "registration_number", "vin", "make", "model", "customer", "current_status", "current_mileage", "current_service_order"],
        filters: search ? [["Garage Vehicle", "registration_number", "like", `%${search}%`]] : undefined,
        limit: 50,
      }),
  })

export const useVehicle = (name: string) =>
  useQuery({
    queryKey: ["garage-vehicle", name],
    queryFn: () => db.getDoc("Garage Vehicle", name),
    enabled: !!name,
  })

export const useCreateVehicle = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Garage Vehicle", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["garage-vehicles"] }),
  })
}

export const useVehicleHistory = (vehicle: string) =>
  useQuery({
    queryKey: ["vehicle-history", vehicle],
    queryFn: () => call.get("subamaz.api.admin.get_vehicle_history", { vehicle }),
    enabled: !!vehicle,
  })
