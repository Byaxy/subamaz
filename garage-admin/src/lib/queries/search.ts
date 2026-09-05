import { useQuery } from "@tanstack/react-query"
import { call } from "../frappe-client"

export type GlobalSearchResult = {
  doctype: string
  name: string
  label: string
  description: string
  type: string
  route: string
}

export const useGlobalSearch = (query: string, enabled = true) =>
  useQuery<GlobalSearchResult[]>({
    queryKey: ["global-search", query],
    queryFn: () => call.get("subamaz.api.admin.global_search", { query }),
    enabled: enabled && query.trim().length >= 2,
  })
