import { describe, it, expect } from "vitest"

function variance(system: number, physical: number) {
  return physical - system
}

describe("Stock-take variance math", () => {
  it("calculates variance correctly", () => {
    expect(variance(10, 12)).toBe(2)
    expect(variance(10, 8)).toBe(-2)
    expect(variance(0, 5)).toBe(5)
  })

  it("handles system vs physical counts from Bin", () => {
    const bins = [
      { item_code: "ITEM-1", actual_qty: 10 },
      { item_code: "ITEM-2", actual_qty: 0 },
    ]
    const counts: Record<string, string> = { "ITEM-1-WH1": "8", "ITEM-2-WH1": "5" }
    const variances = bins.map((b) => variance(b.actual_qty, parseFloat(counts[`${b.item_code}-WH1`] || "0")))
    expect(variances).toEqual([-2, 5])
  })
})
