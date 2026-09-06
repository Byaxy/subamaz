import { describe, it, expect, vi } from "vitest"
import { renderHook } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"

vi.mock("@/lib/queries/portal", () => ({
	useServiceOrderProgress: () => ({
		data: { message: { name: "SO-001", status: "In Progress", completion_percent: 42, estimated_total: 50000, actual_total: 12000 } },
		isLoading: false,
	}),
	useCustomerTimeline: () => ({
		data: {
			message: [
				{ event_type: "Status Change", description: "Visible entry", timestamp: "2026-09-01 10:00:00", visible_to_customer: 1 },
			],
		},
	}),
	useMyVehicles: () => ({ data: [], isLoading: false }),
	useVehicleDetail: () => ({ data: null, isLoading: false }),
	useQuotation: () => ({ data: null, isLoading: false }),
	useApproveQuotation: () => ({ mutateAsync: vi.fn(), isPending: false }),
	useMyInvoices: () => ({ data: [], isLoading: false }),
	useServiceHistory: () => ({ data: [], isLoading: false }),
	useReceptionRecord: () => ({ data: null, isLoading: false }),
}))

import { useServiceOrderProgress, useCustomerTimeline } from "@/lib/queries/portal"

describe("Progress & timeline aggregation", () => {
	it("renders aggregated progress without raw Job Card names", () => {
		const qc = new QueryClient()
		const wrapper = ({ children }: { children: React.ReactNode }) => (
			<QueryClientProvider client={qc}>{children}</QueryClientProvider>
		)
		const { result: progressRes } = renderHook(() => useServiceOrderProgress("SO-001"), { wrapper })
		expect(progressRes.current.data?.message.completion_percent).toBe(42)
		expect(progressRes.current.data?.message.status).toBe("In Progress")
		expect(JSON.stringify(progressRes.current.data)).not.toContain("Garage Job Card")
		expect(JSON.stringify(progressRes.current.data)).not.toContain("GJC-")
	})

	it("only customer-visible timeline entries returned", () => {
		const qc = new QueryClient()
		const wrapper = ({ children }: { children: React.ReactNode }) => (
			<QueryClientProvider client={qc}>{children}</QueryClientProvider>
		)
		const { result } = renderHook(() => useCustomerTimeline("SO-001"), { wrapper })
		const entries = (result.current.data as any)?.message || result.current.data
		expect(entries.length).toBe(1)
		expect(entries[0].description).toBe("Visible entry")
		expect(entries[0].visible_to_customer).toBe(1)
		expect(JSON.stringify(entries)).not.toContain("Hidden")
	})
})
