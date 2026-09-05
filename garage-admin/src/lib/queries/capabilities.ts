import { useQuery } from "@tanstack/react-query"
import { call } from "../frappe-client"
import type { CapabilityMap } from "../capabilities"

export const useMyCapabilities = () =>
  useQuery<CapabilityMap>({
    queryKey: ["capabilities", "my"],
    queryFn: () => call.get("subamaz.api.access_control.get_my_capabilities"),
  })
