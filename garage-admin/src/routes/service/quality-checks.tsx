import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useJobCardsReadyQA } from "@/lib/queries/service"
import { db } from "@/lib/frappe-client"
import { toast } from "sonner"

export const Route = createFileRoute("/service/quality-checks")({
  component: QualityPage,
})

const ITEMS = ["Road Test", "Engine Checked", "No Oil Leak", "Lights Working", "AC Tested", "Tyres Checked", "Tools Removed", "Vehicle Cleaned"] as const

function QualityPage() {
  const { data, isLoading } = useJobCardsReadyQA()
  const [selected, setSelected] = useState<string | null>(null)
  const [checklist, setChecklist] = useState<{ checklist_item: string; result: string }[]>([])
  const [result, setResult] = useState("Pass")

  const load = async (name: string) => {
    setSelected(name)
    const doc: any = await db.getDoc("Garage Job Card", name)
    setChecklist(doc.quality_checklist || [])
    setResult(doc.qa_result || "Pending")
  }

  const handleSave = async () => {
    if (!selected) return
    try {
      await db.updateDoc("Garage Job Card", selected, { quality_checklist: checklist as any, qa_result: result } as any)
      toast.success("QA saved")
      if (result === "Pass") {
        // Advance to Completed
        await db.updateDoc("Garage Job Card", selected, { status: "Completed" } as any)
        toast.success("Moved to Completed")
      } else if (result === "Fail") {
        await db.updateDoc("Garage Job Card", selected, { status: "Working" } as any)
        toast.success("Sent back to Working")
      }
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="quality-page">
      <h1 className="text-2xl font-bold">Quality Checks</h1>
      <p className="text-muted-foreground">Job Cards in Ready QA</p>

      <Card>
        <CardHeader>
          <CardTitle>Ready QA</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Service Order</TableHead>
                  <TableHead>QA Result</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`qa-row-${r.name}`}>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.service_order}</TableCell>
                    <TableCell>{r.qa_result}</TableCell>
                    <TableCell>
                      <Button size="sm" onClick={() => load(r.name)} data-testid={`qa-open-${r.name}`}>
                        Open
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {(!data || data.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">
                      No Ready QA
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selected && (
        <Card data-testid="qa-detail">
          <CardHeader>
            <CardTitle>{selected}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {ITEMS.map((it) => {
              const row = checklist.find((c) => c.checklist_item === it)
              return (
                <div key={it} className="flex items-center gap-2">
                  <span className="w-40 text-sm">{it}</span>
                  <Select
                    value={row?.result || "Pass"}
                    onValueChange={(v) => {
                      const next = checklist.filter((c) => c.checklist_item !== it)
                      next.push({ checklist_item: it, result: v })
                      setChecklist(next)
                    }}
                  >
                    <SelectTrigger className="w-32" data-testid={`qa-${it}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["Pass", "Fail", "N/A"].map((r) => (
                        <SelectItem key={r} value={r}>
                          {r}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )
            })}
            <div>
              <Label>QA Result</Label>
              <Select value={result} onValueChange={setResult}>
                <SelectTrigger data-testid="qa-result">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["Pending", "Pass", "Fail"].map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSave} data-testid="qa-save">
              Save QA
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
