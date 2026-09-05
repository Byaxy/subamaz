import { Link, useRouterState } from "@tanstack/react-router"
import { cn } from "@/lib/utils"
import type { CapabilityMap } from "@/lib/capabilities"
import { LayoutDashboard, Wrench, Users, Package, ShoppingCart, Wallet, UsersRound, BarChart3, Settings } from "lucide-react"

type NavItem = {
  label: string
  to: string
  icon: React.ComponentType<{ className?: string }>
  capability?: string
}

type NavGroup = {
  title: string
  capability?: string
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    title: "SERVICE",
    capability: "module:service",
    items: [
      { label: "Guide", to: "/service/guide", icon: Wrench },
      { label: "Receptions", to: "/service/receptions", icon: Wrench },
      { label: "Inspections", to: "/service/inspections", icon: Wrench },
      { label: "Orders", to: "/service/orders", icon: Wrench },
      { label: "Job Cards", to: "/service/job-cards", icon: Wrench },
      { label: "Quality Checks", to: "/service/quality-checks", icon: Wrench },
      { label: "Deliveries", to: "/service/deliveries", icon: Wrench },
    ],
  },
  {
    title: "CUSTOMERS & VEHICLES",
    capability: "module:customers_vehicles",
    items: [
      { label: "Customers", to: "/customers", icon: Users },
      { label: "Vehicles", to: "/vehicles", icon: Users },
    ],
  },
  {
    title: "PARTS & STOCK",
    capability: "module:parts_stock",
    items: [
      { label: "Items", to: "/parts/items", icon: Package },
      { label: "Stock Take", to: "/parts/stock-take", icon: Package },
      { label: "Transfers", to: "/parts/transfers", icon: Package },
      { label: "Warehouses", to: "/parts/warehouses", icon: Package },
      { label: "Restock", to: "/parts/restock", icon: Package },
    ],
  },
  {
    title: "PROCUREMENT",
    capability: "module:procurement",
    items: [
      { label: "Guide", to: "/procurement/guide", icon: ShoppingCart },
      { label: "Supplier Quotations", to: "/procurement/supplier-quotations", icon: ShoppingCart },
      { label: "Purchase Orders", to: "/procurement/purchase-orders", icon: ShoppingCart },
      { label: "Purchase Invoices", to: "/procurement/purchase-invoices", icon: ShoppingCart },
      { label: "Purchase Receipts", to: "/procurement/purchase-receipts", icon: ShoppingCart },
    ],
  },
  {
    title: "RECORDS & MONEY",
    capability: "module:records_money",
    items: [
      { label: "Invoices", to: "/records/invoices", icon: Wallet },
      { label: "Payments", to: "/records/payments", icon: Wallet },
      { label: "Quotations", to: "/records/quotations", icon: Wallet },
      { label: "Customer Statement", to: "/records/customer-statement", icon: Wallet },
      { label: "Petty Cash", to: "/records/petty-cash", icon: Wallet },
    ],
  },
  {
    title: "STAFF",
    capability: "module:staff",
    items: [
      { label: "Technicians", to: "/staff/technicians", icon: UsersRound },
      { label: "Roles", to: "/staff/roles", icon: UsersRound },
    ],
  },
  {
    title: "INSIGHTS",
    capability: "module:insights",
    items: [{ label: "Reports", to: "/insights/reports", icon: BarChart3 }],
  },
  {
    title: "SETUP",
    capability: "module:setup",
    items: [
      { label: "Garage Settings", to: "/setup/garage-settings", icon: Settings },
      { label: "Access Control", to: "/setup/access-control", icon: Settings },
      { label: "Departments", to: "/setup/departments", icon: Settings },
      { label: "Checklist Templates", to: "/setup/checklist-templates", icon: Settings },
    ],
  },
]

export function Sidebar({ capabilities }: { capabilities: CapabilityMap }) {
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  const isActive = (to: string) => currentPath === to || currentPath.startsWith(to + "/")

  return (
    <aside
      className="flex w-64 flex-col border-r overflow-auto"
      style={{ background: "var(--app-sidebar-bg)", color: "var(--app-sidebar-text)" }}
      data-testid="sidebar"
    >
      <div className="p-4 border-b">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg">
          <span className="size-8 rounded bg-[var(--app-primary)] text-white flex items-center justify-center">GM</span>
          SubaMaz
        </Link>
      </div>

      {/* Overview pinned */}
      <div className="p-2">
        <Link
          to="/"
          data-testid="nav-overview"
          className={cn(
            "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
            isActive("/") && currentPath === "/"
              ? "bg-[var(--app-sidebar-active-bg)] text-[var(--app-sidebar-active-text)]"
              : "hover:bg-black/5"
          )}
        >
          <LayoutDashboard className="size-4" />
          Overview
        </Link>
      </div>

      <div className="flex-1 space-y-4 p-2 overflow-auto">
        {navGroups.map((group) => {
          const enabled = !group.capability || capabilities[group.capability]
          if (!enabled) return null
          return (
            <div key={group.title} data-testid={`group-${group.title}`}>
              <h4 className="mb-1 px-3 text-xs font-semibold uppercase tracking-wider opacity-60">{group.title}</h4>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <Link
                    key={item.to}
                    to={item.to}
                    data-testid={`nav-${item.to}`}
                    className={cn(
                      "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors",
                      isActive(item.to)
                        ? "bg-[var(--app-sidebar-active-bg)] text-[var(--app-sidebar-active-text)]"
                        : "hover:bg-black/5"
                    )}
                  >
                    <item.icon className="size-4" />
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      <div className="p-3 border-t text-xs opacity-60">Garage Admin</div>
    </aside>
  )
}
