import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { db, call } from "../frappe-client"

export const useEmployees = () =>
  useQuery({
    queryKey: ["staff", "employees"],
    queryFn: () => db.getDocList("Employee", { fields: ["name", "employee_name", "first_name", "last_name", "department", "designation", "status"], limit: 50 }),
  })

export const useUsers = () =>
  useQuery({
    queryKey: ["staff", "users"],
    queryFn: () => db.getDocList("User", { fields: ["name", "full_name", "enabled", "user_type"], limit: 50 }),
  })

export const useUserRoles = (user: string) =>
  useQuery({
    queryKey: ["staff", "user-roles", user],
    queryFn: () => db.getDoc("User", user),
    enabled: !!user,
  })

export const useUpdateUserRoles = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ user, roles }: { user: string; roles: string[] }) =>
      db.updateDoc("User", user, { roles: roles.map((r) => ({ role: r })) } as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["staff", "users"] }),
  })
}

export const useTechnicianPerformance = (technician?: string) =>
  useQuery({
    queryKey: ["staff", "performance", technician],
    queryFn: () => call.get("subamaz.api.reports.run_report", { report_name: "Technician Productivity", filters: technician ? { technician } : {} } as any),
    enabled: !!technician || true,
  })
