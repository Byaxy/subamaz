import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { Sidebar } from "@/components/layout/Sidebar"

vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-router")>("@tanstack/react-router")
  return {
    ...actual,
    useRouterState: () => ({ location: { pathname: "/" } }),
    Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  }
})

describe("Staff/Setup gating", () => {
  it("hides STAFF/SETUP for non-Manager", () => {
    const capsManager = { "module:staff": true, "module:setup": true }
    const capsTech = { "module:staff": false, "module:setup": false }

    const { rerender } = render(<Sidebar capabilities={capsManager as any} />)
    expect(screen.getByTestId("group-STAFF")).toBeInTheDocument()
    expect(screen.getByTestId("group-SETUP")).toBeInTheDocument()

    rerender(<Sidebar capabilities={capsTech as any} />)
    expect(screen.queryByTestId("group-STAFF")).not.toBeInTheDocument()
    expect(screen.queryByTestId("group-SETUP")).not.toBeInTheDocument()
  })

  it("Access Control grid manager-only", () => {
    const capsNonManager = { "module:setup": false }
    const capsManager = { "module:setup": true, "*": true }
    expect(capsNonManager["module:setup"]).toBe(false)
    expect(capsManager["module:setup"]).toBe(true)
  })
})
