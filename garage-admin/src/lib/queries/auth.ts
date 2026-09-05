import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { auth, call } from "../frappe-client"

export const useLogin = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      auth.loginWithUsernamePassword({ username, password }),
    onSuccess: () => {
      qc.invalidateQueries()
    },
  })
}

export const useLogout = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => auth.logout(),
    onSuccess: () => {
      qc.clear()
    },
  })
}

export const useLoggedUser = () =>
  useQuery({
    queryKey: ["auth", "logged-user"],
    queryFn: () => call.get("frappe.auth.get_logged_user"),
    retry: false,
  })
