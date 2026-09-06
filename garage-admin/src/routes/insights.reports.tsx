import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { call } from "@/lib/frappe-client"
import { toast } from "sonner"

export const Route = createFileRoute("/insights/reports")({
  component: ReportsPage,
})

const CATEGORIES = {
  SERVICE: ["Job Turnaround Time", "Jobs Completed", "Technician Productivity", "Repairs by Type"],
  "PARTS & STOCK": ["Parts Usage", "Slow Moving Parts", "Stock Count Variance", "Stock Transfers"],
  MONEY: ["Revenue by Month", "Payment Summary", "Outstanding Receivables", "Customer Statement Summary"],
} as const

function ReportsPage() {
  const { data: caps } = useMyCapabilities()
  const [category, setCategory] = useState<keyof typeof CATEGORIES>("SERVICE")
  const [report, setReport] = useState<string>("Job Turnaround Time")
  const [fromDate, setFromDate] = useState("")
  const [toDate, setToDate] = useState("")
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const canSee = (cat: string) => {
    if (cat === "SERVICE") return caps?.["module:service"]
    if (cat === "PARTS & STOCK") return caps?.["module:parts_stock"]
    if (cat === "MONEY") return caps?.["module:records_money"] || caps?.["module:insights"]
    return true
  }

  const handleRun = async () => {
    setLoading(true)
    try {
      const res: any = await call.get("subamaz.api.reports.run_report", { report_name: report, filters: { from_date: fromDate || undefined, to_date: toDate || undefined } } as any)
      setResult(res)
      toast.success("Report run")
    } catch (e: any) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = (type: "Excel" | "PDF") => {
    toast.success(`Export ${type} — native Query Report export (demo)`)
    // In real, would call frappe query_report export endpoint
  }

  return (
    <div className="flex gap-4" data-testid="reports-page">
      <div className="w-64 border rounded p-2 space-y-2">
        <h3 className="font-semibold text-sm">Categories</h3>
        {(Object.keys(CATEGORIES) as Array<keyof typeof CATEGORIES>).map((cat) => (
          <div key={cat} data-testid={`cat-${cat}`}>
            <div className="text-xs font-semibold uppercase opacity-60 mt-2">{cat}</div>
            {CATEGORIES[cat].map((r) => (
              <button
                key={r}
                onClick={() => { setReport(r); setCategory(cat) }}
                className={`w-full text-left text-sm p-1 rounded ${report === r ? "bg-[var(--app-sidebar-active-bg)] text-[var(--app-sidebar-active-text)]" : "hover:bg-muted"}`}
                data-testid={`report-${r}`}
                disabled={!canSee(cat)}
              >
                {r} {!canSee(cat) && "🔒"}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="flex-1 space-y-4">
        <Card>
          <CardHeader><CardTitle>{report}</CardTitle></CardHeader>
          <CardContent className="flex gap-2 items-end">
            <div><Label>From</Label><Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} data-testid="from-date" /></div>
            <div><Label>To</Label><Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} data-testid="to-date" /></div>
            <Button onClick={handleRun} data-testid="run-report">Run</Button>
            <Button variant="outline" onClick={() => handleExport("Excel")} data-testid="export-excel">Excel</Button>
            <Button variant="outline" onClick={() => handleExport("PDF")} data-testid="export-pdf">PDF</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Results</CardTitle></CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-32" /> : result ? (
              <div>
                <Table>
                  <TableHeader><TableRow>{(result.columns || []).map((c: any) => <TableHead key={c.fieldname}>{c.label}</TableHead>)}</TableRow></TableHeader>
                  <TableBody>
                    {(result.result || result.rows || []).slice(0, 50).map((row: any, i: number) => (
                      <TableRow key={i} data-testid={`row-${i}`} className="cursor-pointer hover:bg-muted">
                        {(result.columns || []).map((c: any) => <TableCell key={c.fieldname}>{row[c.fieldname]}</TableCell>)}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {(result.result || []).length === 0 && <div className="text-sm text-muted-foreground text-center">No data</div>}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Select a report and Run</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
