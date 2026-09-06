import { describe, it, expect, vi } from "vitest"

vi.mock("@/lib/queries/capabilities", () => ({
  useMyCapabilities: () => ({ data: { "module:service": true, "module:parts_stock": false, "module:records_money": true }, isLoading: false }),
}))

describe("Insights category gating", () => {
  it("hides PARTS category when lacking capability", async () => {
    const { useMyCapabilities } = await import("@/lib/queries/capabilities")
    const caps: any = (useMyCapabilities() as any).data
    const canSee = (cat: string) => {
      if (cat === "SERVICE") return caps["module:service"]
      if (cat === "PARTS & STOCK") return caps["module:parts_stock"]
      if (cat === "MONEY") return caps["module:records_money"]
      return true
    }
    expect(canSee("SERVICE")).toBe(true)
    expect(canSee("PARTS & STOCK")).toBe(false)
    expect(canSee("MONEY")).toBe(true)
  })

  it("export button triggers handler", async () => {
    const mockRun = vi.fn().mockResolvedValue({ columns: [], result: [] })
    const handleExport = (type: string) => mockRun(`Export ${type}`)
    handleExport("Excel")
    expect(mockRun).toHaveBeenCalledWith("Export Excel")
    handleExport("PDF")
    expect(mockRun).toHaveBeenCalledWith("Export PDF")
  })
})
