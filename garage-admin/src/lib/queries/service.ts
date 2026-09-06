import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { call, db } from "../frappe-client"

// Receptions
export const useReceptions = (status?: string) =>
  useQuery({
    queryKey: ["service", "receptions", status],
    queryFn: () =>
      db.getDocList("Vehicle Reception", {
        fields: ["name", "customer", "vehicle", "reception_date", "status", "customer_complaint"],
        filters: status ? [["Vehicle Reception", "status", "=", status]] : undefined,
        orderBy: { field: "creation", order: "desc" },
        limit: 100,
      }),
  })

export const useReceptionQueue = () =>
  useQuery({
    queryKey: ["service", "receptions", "queue"],
    queryFn: () =>
      db.getDocList("Vehicle Reception", {
        fields: ["name", "customer", "vehicle", "reception_date", "status"],
        filters: [["Vehicle Reception", "status", "=", "Draft — Parked"]],
        limit: 100,
      }),
  })

export const useReception = (name: string) =>
  useQuery({
    queryKey: ["service", "reception", name],
    queryFn: () => db.getDoc("Vehicle Reception", name),
    enabled: !!name,
  })

export const useCreateReception = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: { vehicle: string; customer: string; payload: Record<string, unknown> }) =>
      call.post("subamaz.api.reception.create_reception", payload as any),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["service", "receptions"] })
    },
  })
}

export const useUpdateReception = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, data }: { name: string; data: Record<string, unknown> }) =>
      db.updateDoc("Vehicle Reception", name, data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["service", "receptions"] }),
  })
}

// Vehicles & Customers for walkaround
export const useVehicles = (search?: string) =>
  useQuery({
    queryKey: ["vehicles", search],
    queryFn: () =>
      db.getDocList("Garage Vehicle", {
        fields: ["name", "registration_number", "vin", "customer", "current_status"],
        filters: search ? [["Garage Vehicle", "registration_number", "like", `%${search}%`]] : undefined,
        limit: 20,
      }),
    enabled: search === undefined || search.length >= 2 || !search,
  })

export const useCustomers = (search?: string) =>
  useQuery({
    queryKey: ["customers", search],
    queryFn: () =>
      db.getDocList("Customer", {
        fields: ["name", "customer_name"],
        filters: search ? [["Customer", "customer_name", "like", `%${search}%`]] : undefined,
        limit: 20,
      }),
    enabled: search === undefined || search.length >= 2 || !search,
  })

export const useEmployees = () =>
  useQuery({
    queryKey: ["employees"],
    queryFn: () => db.getDocList("Employee", { fields: ["name", "employee_name", "first_name"], limit: 50 }),
  })

// Inspections
export const useInspections = () =>
  useQuery({
    queryKey: ["service", "inspections"],
    queryFn: () =>
      db.getDocList("Vehicle Inspection", {
        fields: ["name", "vehicle", "customer", "inspector", "inspection_date", "inspection_result", "recommendation"],
        orderBy: { field: "creation", order: "desc" },
        limit: 100,
      }),
  })

export const useInspection = (name: string) =>
  useQuery({
    queryKey: ["service", "inspection", name],
    queryFn: () => db.getDoc("Vehicle Inspection", name),
    enabled: !!name,
  })

export const useCreateInspection = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Vehicle Inspection", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["service", "inspections"] }),
  })
}

// Service Orders
export const useServiceOrders = () =>
  useQuery({
    queryKey: ["service", "orders"],
    queryFn: () =>
      db.getDocList("Service Order", {
        fields: ["name", "customer", "vehicle", "status", "opening_date", "expected_finish", "completion_percent"],
        orderBy: { field: "creation", order: "desc" },
        limit: 100,
      }),
  })

export const useServiceOrder = (name: string) =>
  useQuery({
    queryKey: ["service", "order", name],
    queryFn: () => db.getDoc("Service Order", name),
    enabled: !!name,
  })

// Job Cards
export const useJobCards = () =>
  useQuery({
    queryKey: ["service", "job-cards"],
    queryFn: () =>
      db.getDocList("Garage Job Card", {
        fields: ["name", "service_order", "department", "lead_technician", "status", "priority", "completion_percent"],
        orderBy: { field: "creation", order: "desc" },
        limit: 200,
      }),
  })

export const useJobCard = (name: string) =>
  useQuery({
    queryKey: ["service", "job-card", name],
    queryFn: () => db.getDoc("Garage Job Card", name),
    enabled: !!name,
  })

export const useJobCardActions = () => {
  const qc = useQueryClient()
  const invalidate = () => qc.invalidateQueries({ queryKey: ["service", "job-cards"] })
  return {
    start: useMutation({ mutationFn: (name: string) => call.post("subamaz.api.job_card.start_job", { job_card: name }), onSuccess: invalidate }),
    pause: useMutation({ mutationFn: (name: string) => call.post("subamaz.api.job_card.pause_job", { job_card: name }), onSuccess: invalidate }),
    complete: useMutation({ mutationFn: (name: string) => call.post("subamaz.api.job_card.complete_job", { job_card: name }), onSuccess: invalidate }),
    consume: useMutation({
      mutationFn: (p: { job_card: string; item_code: string; qty: number; warehouse?: string }) =>
        call.post("subamaz.api.job_card.consume_part", p as any),
      onSuccess: invalidate,
    }),
  }
}

// Deliveries
export const useDeliveries = () =>
  useQuery({
    queryKey: ["service", "deliveries"],
    queryFn: () =>
      db.getDocList("Vehicle Delivery", {
        fields: ["name", "vehicle", "customer", "service_order", "delivery_date"],
        orderBy: { field: "creation", order: "desc" },
        limit: 100,
      }),
  })

export const useCreateDelivery = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Vehicle Delivery", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["service", "deliveries"] }),
  })
}

// QA
export const useJobCardsReadyQA = () =>
  useQuery({
    queryKey: ["service", "qa"],
    queryFn: () =>
      db.getDocList("Garage Job Card", {
        fields: ["name", "service_order", "status", "qa_result"],
        filters: [["Garage Job Card", "status", "=", "Ready QA"]],
        limit: 100,
      }),
  })

export const useApproveAdditionalPart = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: { job_card: string; row_name: string; approve: boolean }) =>
      call.post("subamaz.api.qa.approve_additional_part", p as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["service", "job-cards"] }),
  })
}

// Counts for Guide
export const useServiceCounts = () =>
  useQuery({
    queryKey: ["service", "counts"],
    queryFn: async () => {
      const [receptions, inspections, orders, jobs, deliveries, qa] = await Promise.all([
        db.getDocList("Vehicle Reception", { fields: ["name"], limit: 1 }).then((r: any) => r.length),
        db.getDocList("Vehicle Inspection", { fields: ["name"], limit: 1 }).then((r: any) => r.length),
        db.getDocList("Service Order", { fields: ["name"], limit: 1 }).then((r: any) => r.length),
        db.getDocList("Garage Job Card", { fields: ["name"], limit: 1 }).then((r: any) => r.length),
        db.getDocList("Vehicle Delivery", { fields: ["name"], limit: 1 }).then((r: any) => r.length),
        db.getDocList("Garage Job Card", { fields: ["name"], filters: [["Garage Job Card", "status", "=", "Ready QA"]], limit: 1 }).then((r: any) => r.length),
      ])
      // Use count via getDocList is not accurate for total; fallback to count API if available
      // For now use length of limited query as placeholder; real counts via frappe.db.count would be better but we use getDocList with limit 0 trick
      return { receptions, inspections, orders, jobs, deliveries, qa }
    },
  })
