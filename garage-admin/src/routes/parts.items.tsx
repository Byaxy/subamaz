import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { useItems, useStockStatus } from "@/lib/queries/parts"
import { Badge } from "@/components/ui/badge"

export const Route = createFileRoute("/parts/items")({
  component: ItemsPage,
})

function ItemsPage() {
  const [search, setSearch] = useState("")
  const { data: items, isLoading } = useItems(search)
  const { data: stock } = useStockStatus()

  const getStock = (code: string) => {
    const bins: any[] = stock || []
    const bin = bins.find((b: any) => b.item_code === code)
    return bin
  }

  return (
    <div className="space-y-4" data-testid="items-page">
      <h1 className="text-2xl font-bold">Parts — Items</h1>

      <Card>
        <CardHeader>
          <CardTitle>Items & Balances</CardTitle>
          <Input placeholder="Search item_code" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="item-search" />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>UOM</TableHead>
                  <TableHead>Valuation</TableHead>
                  <TableHead>Stock</TableHead>
                  <TableHead>Reorder</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(items || []).map((it: any) => {
                  const bin = getStock(it.item_code)
                  return (
                    <TableRow key={it.item_code} data-testid={`item-${it.item_code}`}>
                      <TableCell className="font-medium">{it.item_code}</TableCell>
                      <TableCell>{it.item_name}</TableCell>
                      <TableCell>{it.stock_uom}</TableCell>
                      <TableCell>{it.valuation_rate}</TableCell>
                      <TableCell>
                        {bin ? `${bin.actual_qty} @ ${bin.warehouse}` : "—"}
                        {bin && bin.actual_qty < (bin.reorder_level || 0) && <Badge variant="destructive" className="ml-2">Low</Badge>}
                      </TableCell>
                      <TableCell>{bin?.reorder_level ?? "—"}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
