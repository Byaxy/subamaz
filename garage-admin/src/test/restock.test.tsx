import { describe, it, expect } from "vitest"

function groupBySupplier(lowItems: Array<{ supplier: string; item_code: string }>) {
  const groups: Record<string, typeof lowItems> = {}
  for (const it of lowItems) {
    groups[it.supplier] = groups[it.supplier] || []
    groups[it.supplier].push(it)
  }
  return Object.entries(groups).map(([supplier, items]) => ({ supplier, items, total_items: items.length }))
}

describe("Restock grouping", () => {
  it("produces correct number of draft POs per supplier", () => {
    const lowItems = [
      { supplier: "Supplier A", item_code: "ITEM-1" },
      { supplier: "Supplier A", item_code: "ITEM-2" },
      { supplier: "Supplier B", item_code: "ITEM-3" },
    ]
    const groups = groupBySupplier(lowItems)
    expect(groups.length).toBe(2)
    expect(groups.find((g) => g.supplier === "Supplier A")?.total_items).toBe(2)
    expect(groups.find((g) => g.supplier === "Supplier B")?.total_items).toBe(1)
  })

  it("handles No Supplier fallback", () => {
    const lowItems = [
      { supplier: "No Supplier", item_code: "ITEM-1" },
      { supplier: "No Supplier", item_code: "ITEM-2" },
    ]
    const groups = groupBySupplier(lowItems)
    expect(groups.length).toBe(1)
    expect(groups[0].supplier).toBe("No Supplier")
  })
})
