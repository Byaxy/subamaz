import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { Sidebar } from "./Sidebar"

vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-router")>("@tanstack/react-router")
  return {
    ...actual,
    useRouterState: () => ({ location: { pathname: "/" } }),
    Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  }
})

describe("Sidebar", () => {
  it("renders only enabled module groups", () => {
    const capabilities = {
      "module:service": true,
      "module:customers_vehicles": false,
      "module:parts_stock": true,
      "module:procurement": false,
      "module:records_money": false,
      "module:staff": false,
      "module:insights": true,
      "module:setup": false,
    }

    render(<Sidebar capabilities={capabilities} />)

    expect(screen.getByTestId("group-SERVICE")).toBeInTheDocument()
    expect(screen.queryByTestId("group-CUSTOMERS & VEHICLES")).not.toBeInTheDocument()
    expect(screen.getByTestId("group-PARTS & STOCK")).toBeInTheDocument()
    expect(screen.queryByTestId("group-PROCUREMENT")).not.toBeInTheDocument()
    expect(screen.getByTestId("group-INSIGHTS")).toBeInTheDocument()
    expect(screen.queryByTestId("group-SETUP")).not.toBeInTheDocument()
  })

  it("renders overview pinned", () => {
    render(<Sidebar capabilities={{}} />)
    expect(screen.getByTestId("nav-overview")).toBeInTheDocument()
  })
})
