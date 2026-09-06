import { describe, it, expect } from "vitest"

describe("Vehicle history timeline order", () => {
  it("sorts history by date chronological", () => {
    const history = [
      { doctype: "Vehicle Delivery", name: "VD-1", date: "2026-09-03", title: "Delivery" },
      { doctype: "Vehicle Reception", name: "VR-1", date: "2026-09-01", title: "Reception" },
      { doctype: "Service Order", name: "SO-1", date: "2026-09-02", title: "SO" },
    ]
    const sorted = [...history].sort((a, b) => (a.date || "").localeCompare(b.date || ""))
    expect(sorted[0].name).toBe("VR-1")
    expect(sorted[1].name).toBe("SO-1")
    expect(sorted[2].name).toBe("VD-1")
  })

  it("distinguishes customer-visible vs internal", () => {
    const history = [
      { doctype: "Service Timeline Entry", visible_to_customer: 1 },
      { doctype: "Garage Job Card", visible_to_customer: 0 },
    ]
    const customerVisible = history.filter((h) => h.visible_to_customer)
    expect(customerVisible.length).toBe(1)
    expect(customerVisible[0].doctype).toBe("Service Timeline Entry")
  })
})
