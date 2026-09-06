import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const mockNavigate = vi.fn()
const mockMutateAsync = vi.fn().mockResolvedValue({})

vi.mock("@tanstack/react-router", async () => {
	const actual = await vi.importActual<typeof import("@tanstack/react-router")>("@tanstack/react-router")
	return {
		...actual,
		useNavigate: () => mockNavigate,
		useRouterState: () => ({ location: { pathname: "/" } }),
	}
})

vi.mock("@/lib/queries/auth", () => ({
	useLogin: () => ({
		mutateAsync: mockMutateAsync,
		isPending: false,
	}),
	useLogout: () => ({ mutateAsync: vi.fn() }),
	useLoggedUser: () => ({ data: "test@portal.com", isLoading: false, isError: false }),
}))

import { LoginPage } from "@/routes/login"

describe("Portal login mutation", () => {
	beforeEach(() => {
		vi.clearAllMocks()
		mockMutateAsync.mockResolvedValue({})
	})

	it("calls login mutation with username/password on submit", async () => {
		const qc = new QueryClient()
		render(
			<QueryClientProvider client={qc}>
				<LoginPage />
			</QueryClientProvider>
		)

		expect(await screen.findByTestId("portal-login")).toBeInTheDocument()

		fireEvent.change(screen.getByTestId("login-email"), { target: { value: "customer@example.com" } })
		fireEvent.change(screen.getByTestId("login-password"), { target: { value: "secret123" } })
		fireEvent.click(screen.getByTestId("login-submit"))

		await waitFor(() => expect(mockMutateAsync).toHaveBeenCalledWith({ username: "customer@example.com", password: "secret123" }))
	})

	it("navigates to / on successful login", async () => {
		const qc = new QueryClient()
		render(
			<QueryClientProvider client={qc}>
				<LoginPage />
			</QueryClientProvider>
		)
		fireEvent.change(screen.getByTestId("login-email"), { target: { value: "a@b.com" } })
		fireEvent.change(screen.getByTestId("login-password"), { target: { value: "pw" } })
		fireEvent.click(screen.getByTestId("login-submit"))
		await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith({ to: "/" }))
	})
})
