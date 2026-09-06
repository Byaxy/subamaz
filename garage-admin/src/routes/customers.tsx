import { createFileRoute, Link } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useCustomers, useCreateCustomer } from "@/lib/queries/customers"
import { toast } from "sonner"

export const Route = createFileRoute("/customers")({
  component: CustomersPage,
})

function CustomersPage() {
  const [search, setSearch] = useState("")
  const { data, isLoading } = useCustomers(search)
  const create = useCreateCustomer()
  const [form, setForm] = useState({ customer_name: "", customer_group: "" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({ customer_name: form.customer_name, customer_type: "Individual" } as any)
      toast.success("Customer created")
      setForm({ customer_name: "", customer_group: "" })
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="customers-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Customers</h1>
        <Button asChild variant="outline">
          <Link to="/records/customer-statement">Statement</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create Customer</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input placeholder="Customer name" value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} data-testid="customer-name" />
          <Button onClick={handleCreate} data-testid="create-customer">
            Create
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>List</CardTitle>
          <div className="flex gap-2">
            <Input placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="customer-search" />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Customer Name</TableHead>
                  <TableHead>Group</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((c: any) => (
                  <TableRow key={c.name} data-testid={`customer-${c.name}`}>
                    <TableCell>{c.name}</TableCell>
                    <TableCell>{c.customer_name}</TableCell>
                    <TableCell>{c.customer_group}</TableCell>
                    <TableCell>
                      <Button asChild size="sm" variant="outline">
                        <Link to="/vehicles" search={{ customer: c.name } as any}>
                          Vehicles
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
