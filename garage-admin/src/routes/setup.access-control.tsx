import { createFileRoute } from "@tanstack/react-router"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useAccessControlGrid, useSaveAccessGrid } from "@/lib/queries/setup"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { toast } from "sonner"

export const Route = createFileRoute("/setup/access-control")({
  component: AccessControlPage,
})

function AccessControlPage() {
  const { data, isLoading } = useAccessControlGrid()
  const save = useSaveAccessGrid()
  const { data: caps } = useMyCapabilities()
  const isManager = !!caps?.["*"] || false // Manager has *, but we check via API error; for UI, check if grid loaded
  // Alternative: check if user is Manager via capabilities? We can just try to show grid, and if not Manager, show denied
  const [changes, setChanges] = useState<Record<string, number>>({})
  const [tab, setTab] = useState<"Module" | "Action">("Module")

  // data shape: {roles, capabilities, grid: [{role, capability, label, capability_type, in_ceiling, enabled}]}
  const grid: any[] = (data as any)?.grid || []
  const capabilities: any[] = (data as any)?.capabilities || []
  const roles: string[] = (data as any)?.roles || []

  const filteredCaps = capabilities.filter((c: any) => c.capability_type === tab)
  const getCell = (role: string, cap: string) => grid.find((g: any) => g.role === role && g.capability === cap)

  const toggle = (role: string, cap: string, inCeiling: number, enabled: number) => {
    if (!inCeiling) return
    const key = `${role}::${cap}`
    const current = changes[key] !== undefined ? changes[key] : enabled
    setChanges({ ...changes, [key]: current ? 0 : 1 })
  }

  const handleSave = async () => {
    const payload = Object.entries(changes).map(([k, v]) => {
      const [role, cap] = k.split("::")
      return { role, capability: cap, enabled: v }
    })
    if (payload.length === 0) {
      toast.success("No changes")
      return
    }
    try {
      await save.mutateAsync(payload)
      toast.success("Saved")
      setChanges({})
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  if (isLoading) return <Skeleton className="h-64" />

  // If not Manager, the API would have thrown PermissionError, but we still show UI with denied message
  // We check if grid is empty and user is not Manager
  const isDenied = !isLoading && grid.length === 0

  return (
    <div className="space-y-4" data-testid="access-control-page">
      <h1 className="text-2xl font-bold">Access Control</h1>
      <p className="text-muted-foreground">Modules/Actions tabs — role × capability grid — “—” for unavailable</p>

      {isDenied ? (
        <Card><CardContent className="p-4"><Badge variant="destructive">Only Garage Manager can view</Badge></CardContent></Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Grid</CardTitle>
            <CardDescription>Cells marked ‘—’ aren't available to that role's level. Backend safety rules still apply on top of these choices.</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={tab} onValueChange={(v) => setTab(v as any)}>
              <TabsList data-testid="ac-tabs">
                <TabsTrigger value="Module" data-testid="tab-modules">Modules</TabsTrigger>
                <TabsTrigger value="Action" data-testid="tab-actions">Actions</TabsTrigger>
              </TabsList>
              <TabsContent value={tab} className="overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Capability</TableHead>
                      {roles.map((r) => <TableHead key={r}>{r}</TableHead>)}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredCaps.map((cap: any) => (
                      <TableRow key={cap.capability_key} data-testid={`cap-${cap.capability_key}`}>
                        <TableCell className="font-medium">{cap.label} <span className="text-xs text-muted-foreground">({cap.capability_key})</span></TableCell>
                        {roles.map((role) => {
                          const cell = getCell(role, cap.capability_key)
                          const inCeiling = cell?.in_ceiling
                          const enabled = cell ? (changes[`${role}::${cap.capability_key}`] !== undefined ? changes[`${role}::${cap.capability_key}`] : cell.enabled) : 0
                          return (
                            <TableCell key={role} data-testid={`cell-${role}-${cap.capability_key}`}>
                              {inCeiling ? (
                                <Checkbox checked={!!enabled} onCheckedChange={() => toggle(role, cap.capability_key, inCeiling, cell.enabled)} data-testid={`toggle-${role}-${cap.capability_key}`} />
                              ) : (
                                <span>—</span>
                              )}
                            </TableCell>
                          )
                        })}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>
            </Tabs>
            <div className="mt-4 flex justify-between items-center">
              <span className="text-xs text-muted-foreground">* Cells marked ‘—’ aren't available to that role's level. Backend safety rules still apply on top of these choices.</span>
              <Button onClick={handleSave} disabled={Object.keys(changes).length === 0 || save.isPending} data-testid="save-ac">Save changes</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
