export type CapabilityKey = string

export type CapabilityMap = Record<string, boolean>

export function hasModule(capabilities: CapabilityMap | undefined, key: string): boolean {
  if (!capabilities) return false
  return !!capabilities[key]
}

export const MODULE_KEYS = [
  "module:service",
  "module:customers_vehicles",
  "module:parts_stock",
  "module:procurement",
  "module:records_money",
  "module:staff",
  "module:insights",
  "module:setup",
] as const

export function filterModules(capabilities: CapabilityMap) {
  return MODULE_KEYS.filter((k) => capabilities[k])
}
