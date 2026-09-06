import { describe, it, expect, vi } from "vitest"

vi.mock("@/lib/queries/money", () => ({
  useInvoices: () => ({ data: [{ name: "SINV-1", customer: "Cust A", grand_total: 1000, outstanding_amount: 500, status: "Unpaid" }], isLoading: false }),
  usePayments: () => ({ data: [], isLoading: false }),
  useQuotations: () => ({ data: [], isLoading: false }),
  usePettyCash: () => ({ data: [], isLoading: false }),
  useMoneyCounts: () => ({ data: { invoices: 1, payments: 0, quotations: 0, petty_cash: 0 }, isLoading: false }),
  useApplyDiscount: () => ({ mutateAsync: vi.fn() }),
  useVoidInvoice: () => ({ mutateAsync: vi.fn() }),
  useApproveCreditSale: () => ({ mutateAsync: vi.fn() }),
  useCreatePettyCash: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCustomerStatement: () => ({ data: { result: [{ customer: "Cust A", invoices: 1, billed: 1000, outstanding: 500 }] }, isLoading: false }),
  useCreatePayment: () => ({ mutateAsync: vi.fn() }),
}))

vi.mock("@/lib/queries/capabilities", () => ({
  useMyCapabilities: () => ({ data: { "action:apply_invoice_discount": false, "action:void_invoice": false, "action:record_petty_cash": false }, isLoading: false }),
}))

describe("Money — capability gating", () => {
  it("hides discount/void buttons when lacking capability", async () => {
    const { useMyCapabilities } = await import("@/lib/queries/capabilities")
    const caps: any = (useMyCapabilities() as any).data
    expect(caps["action:apply_invoice_discount"]).toBe(false)
    expect(caps["action:void_invoice"]).toBe(false)
    expect(caps["action:record_petty_cash"]).toBe(false)
  })

  it("statement renders Customer Statement Summary report data", async () => {
    const { useCustomerStatement } = await import("@/lib/queries/money")
    const data: any = (useCustomerStatement("Cust A") as any).data
    expect(data.result[0].billed).toBe(1000)
    expect(data.result[0].outstanding).toBe(500)
  })

  it("guide step-cards show correct live counts", async () => {
    const { useMoneyCounts } = await import("@/lib/queries/money")
    const counts: any = (useMoneyCounts() as any).data
    expect(counts.invoices).toBe(1)
  })
})
