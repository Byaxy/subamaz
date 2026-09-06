import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { call, db } from "../frappe-client"

export const useGarageSettings = () =>
  useQuery({
    queryKey: ["setup", "garage-settings"],
    queryFn: () => db.getDoc("Garage Settings", "Garage Settings"),
  })

export const useUpdateGarageSettings = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => call.post("subamaz.api.admin.update_garage_settings", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["setup", "garage-settings"] }),
  })
}

export const useDepartments = () =>
  useQuery({
    queryKey: ["setup", "departments"],
    queryFn: () => db.getDocList("Garage Department", { fields: ["name", "department_name", "default_hourly_rate", "is_active"], limit: 50 }),
  })

export const useCreateDepartment = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Garage Department", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["setup", "departments"] }),
  })
}

export const useUpdateDepartment = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, data }: { name: string; data: Record<string, unknown> }) => db.updateDoc("Garage Department", name, data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["setup", "departments"] }),
  })
}

export const useChecklistTemplates = () =>
  useQuery({
    queryKey: ["setup", "checklist-templates"],
    queryFn: () => db.getDocList("Service Checklist Template", { fields: ["name", "template_name", "applies_to"], limit: 50 }),
  })

export const useChecklistTemplate = (name: string) =>
  useQuery({
    queryKey: ["setup", "checklist-template", name],
    queryFn: () => db.getDoc("Service Checklist Template", name),
    enabled: !!name,
  })

export const useCreateChecklistTemplate = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => db.createDoc("Service Checklist Template", data as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["setup", "checklist-templates"] }),
  })
}

export const useAccessControlGrid = () =>
  useQuery({
    queryKey: ["setup", "access-grid"],
    queryFn: () => call.get("subamaz.api.access_control.get_access_control_grid"),
  })

export const useSaveAccessGrid = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (changes: Array<{ role: string; capability: string; enabled: number }>) =>
      call.post("subamaz.api.access_control.save_access_control_grid", { changes } as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["setup", "access-grid"] }),
  })
}
