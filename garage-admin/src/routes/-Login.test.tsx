import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { LoginPage } from "./login"

const mockMutateAsync = vi.fn().mockResolvedValue({})
const mockNavigate = vi.fn()

vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-router")>("@tanstack/react-router")
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock("@/lib/queries/auth", () => ({
  useLogin: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
  useLogout: () => ({ mutateAsync: vi.fn() }),
  useLoggedUser: () => ({ data: null }),
}))

describe("Login", () => {
  it("calls login mutation on submit", async () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <LoginPage />
      </QueryClientProvider>
    )

    expect(await screen.findByTestId("login-page")).toBeInTheDocument()

    const email = screen.getByTestId("login-email")
    const password = screen.getByTestId("login-password")
    const submit = screen.getByTestId("login-submit")

    fireEvent.change(email, { target: { value: "manager@test.com" } })
    fireEvent.change(password, { target: { value: "password" } })
    fireEvent.click(submit)

    await waitFor(() => expect(mockMutateAsync).toHaveBeenCalledWith({ username: "manager@test.com", password: "password" }))
  })
})
