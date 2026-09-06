import { describe, it, expect, vi } from "vitest"
import { render, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const mockNavigate = vi.fn()

vi.mock("@tanstack/react-router", async () => {
	const actual = await vi.importActual<typeof import("@tanstack/react-router")>("@tanstack/react-router")
	return {
		...actual,
		useNavigate: () => mockNavigate,
		useRouterState: () => ({ location: { pathname: "/" } }),
		Link: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
	}
})

vi.mock("@/lib/queries/auth", () => ({
	useLogin: () => ({ mutateAsync: vi.fn(), isPending: false }),
	useLogout: () => ({ mutateAsync: vi.fn() }),
	useLoggedUser: () => ({ data: "Guest", isLoading: false, isError: false }),
}))

import { PortalShell } from "@/components/layout/PortalShell"

describe("Portal guard redirect", () => {
	it("redirects to /login when unauthenticated", async () => {
		const qc = new QueryClient()
		render(
			<QueryClientProvider client={qc}>
				<PortalShell>
					<div>child</div>
				</PortalShell>
			</QueryClientProvider>
		)
		await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith({ to: "/login" }))
	})
})
