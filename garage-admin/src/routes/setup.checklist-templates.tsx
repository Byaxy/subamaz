import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useChecklistTemplates, useCreateChecklistTemplate } from "@/lib/queries/setup"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"

export const Route = createFileRoute("/setup/checklist-templates")({
  component: ChecklistPage,
})

function ChecklistPage() {
  const { data, isLoading } = useChecklistTemplates()
  const create = useCreateChecklistTemplate()
  const { data: caps } = useMyCapabilities()
  const canEdit = !!caps?.["action:change_settings"]
  const [form, setForm] = useState({ template_name: "", applies_to: "Inspection", items: [] as any[] })
  const [item, setItem] = useState({ item_description: "", default_expected_result: "" })

  const handleCreate = async () => {
    try {
      await create.mutateAsync({ template_name: form.template_name, applies_to: form.applies_to, items: form.items } as any)
      toast.success("Created")
      setForm({ template_name: "", applies_to: "Inspection", items: [] })
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <div className="space-y-4" data-testid="checklist-templates-page">
      <h1 className="text-2xl font-bold">Checklist Templates</h1>
      {!canEdit && <Badge variant="destructive">Read only — action:change_settings required</Badge>}

      <Card>
        <CardHeader><CardTitle>Create Template</CardTitle></CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="grid gap-2 md:grid-cols-3">
            <div><Label>Name</Label><Input value={form.template_name} onChange={(e) => setForm({ ...form, template_name: e.target.value })} data-testid="tmpl-name" /></div>
            <div><Label>Applies To</Label><Select value={form.applies_to} onValueChange={(v) => setForm({ ...form, applies_to: v })}><SelectTrigger data-testid="tmpl-applies"><SelectValue /></SelectTrigger><SelectContent>{["Inspection", "Repair", "Delivery", "QA"].map((a) => <SelectItem key={a} value={a}>{a}</SelectItem>)}</SelectContent></Select></div>
            <div className="flex items-end"><Button onClick={handleCreate} disabled={!canEdit} data-testid="create-tmpl">Create</Button></div>
          </div>
          <div className="border p-2 rounded flex gap-2">
            <Input placeholder="Item" value={item.item_description} onChange={(e) => setItem({ ...item, item_description: e.target.value })} data-testid="item-desc" />
            <Input placeholder="Expected" value={item.default_expected_result} onChange={(e) => setItem({ ...item, default_expected_result: e.target.value })} data-testid="item-expected" />
            <Button onClick={() => { setForm({ ...form, items: [...form.items, item] }); setItem({ item_description: "", default_expected_result: "" }) }} data-testid="add-item">Add</Button>
          </div>
          <div data-testid="item-count">Items: {form.items.length}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>List</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-32" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Applies To</TableHead></TableRow></TableHeader>
              <TableBody>
                {(data || []).map((r: any) => (
                  <TableRow key={r.name} data-testid={`tmpl-${r.name}`}>
                    <TableCell>{r.template_name}</TableCell><TableCell>{r.applies_to}</TableCell>
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
