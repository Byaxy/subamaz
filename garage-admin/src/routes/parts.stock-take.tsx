import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useStockStatus } from "@/lib/queries/parts"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { toast } from "sonner"

export const Route = createFileRoute("/parts/stock-take")({
  component: StockTakePage,
})

function StockTakePage() {
  const { data, isLoading } = useStockStatus()
  const [counts, setCounts] = useState<Record<string, string>>({})

  const handleVariance = (item_code: string, warehouse: string) => {
    const bin: any = (data || []).find((b: any) => b.item_code === item_code && b.warehouse === warehouse)
    const entered = parseFloat(counts[`${item_code}-${warehouse}`] || "0")
    const system = bin?.actual_qty || 0
    return entered - system
  }

  return (
    <div className="space-y-4" data-testid="stock-take-page">
      <h1 className="text-2xl font-bold">Stock Take</h1>
      <p className="text-muted-foreground">Compare system vs physical count — feeds Stock Count Variance report</p>

      <Card>
        <CardHeader>
          <CardTitle>Count Entry</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item</TableHead>
                  <TableHead>Warehouse</TableHead>
                  <TableHead>System</TableHead>
                  <TableHead>Physical Count</TableHead>
                  <TableHead>Variance</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).slice(0, 50).map((b: any) => (
                  <TableRow key={`${b.item_code}-${b.warehouse}`} data-testid={`bin-${b.item_code}`}>
                    <TableCell>{b.item_code}</TableCell>
                    <TableCell>{b.warehouse}</TableCell>
                    <TableCell>{b.actual_qty}</TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={counts[`${b.item_code}-${b.warehouse}`] || ""}
                        onChange={(e) => setCounts({ ...counts, [`${b.item_code}-${b.warehouse}`]: e.target.value })}
                        className="w-24"
                        data-testid={`count-${b.item_code}`}
                      />
                    </TableCell>
                    <TableCell>{handleVariance(b.item_code, b.warehouse)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <Button className="mt-4" onClick={() => toast.success("Stock take saved (demo)")} data-testid="save-take">
            Save
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
