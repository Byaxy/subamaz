import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { useGarageSettings, useUpdateGarageSettings } from "@/lib/queries/setup"
import { useMyCapabilities } from "@/lib/queries/capabilities"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"

export const Route = createFileRoute("/setup/garage-settings")({
  component: GarageSettingsPage,
})

function GarageSettingsPage() {
  const { data, isLoading } = useGarageSettings()
  const update = useUpdateGarageSettings()
  const { data: caps } = useMyCapabilities()
  const canEdit = !!caps?.["action:change_settings"]
  const [form, setForm] = useState<any>({})

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  const handleSave = async () => {
    try {
      await update.mutateAsync(form)
      toast.success("Saved")
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  if (isLoading) return <Skeleton className="h-64" />

  return (
    <div className="space-y-4" data-testid="garage-settings-page">
      <h1 className="text-2xl font-bold">Garage Settings</h1>
      {!canEdit && <Badge variant="destructive">No capability — read only (action:change_settings required)</Badge>}

      <Card>
        <CardHeader><CardTitle>Thresholds & Survey</CardTitle><CardDescription>Gated by action:change_settings</CardDescription></CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div><Label>Project Duration Threshold (days)</Label><Input type="number" value={form.project_duration_threshold_days || ""} onChange={(e) => setForm({ ...form, project_duration_threshold_days: parseInt(e.target.value) || 0 })} disabled={!canEdit} data-testid="threshold-days" /></div>
          <div><Label>Project Cost Threshold</Label><Input type="number" value={form.project_cost_threshold || ""} onChange={(e) => setForm({ ...form, project_cost_threshold: parseFloat(e.target.value) || 0 })} disabled={!canEdit} data-testid="threshold-cost" /></div>
          <div><Label>Reminder Mileage Interval</Label><Input type="number" value={form.reminder_mileage_interval || ""} onChange={(e) => setForm({ ...form, reminder_mileage_interval: parseInt(e.target.value) || 0 })} disabled={!canEdit} data-testid="reminder-mileage" /></div>
          <div><Label>Reminder Days Interval</Label><Input type="number" value={form.reminder_days_interval || ""} onChange={(e) => setForm({ ...form, reminder_days_interval: parseInt(e.target.value) || 0 })} disabled={!canEdit} data-testid="reminder-days" /></div>
          <div><Label>Required Arrival Photos (comma)</Label><Input value={form.reception_photo_requirements || ""} onChange={(e) => setForm({ ...form, reception_photo_requirements: e.target.value })} disabled={!canEdit} data-testid="photo-req" /></div>
          <div>
            <Label>Enable Satisfaction Survey</Label>
            <select value={form.enable_satisfaction_survey ? "1" : "0"} onChange={(e) => setForm({ ...form, enable_satisfaction_survey: e.target.value === "1" })} disabled={!canEdit} className="w-full border rounded p-2" data-testid="enable-survey">
              <option value="1">Yes</option><option value="0">No</option>
            </select>
          </div>
          <div className="md:col-span-2"><Label>Survey Email Body</Label><Textarea value={form.survey_email_body || ""} onChange={(e) => setForm({ ...form, survey_email_body: e.target.value })} disabled={!canEdit} data-testid="survey-body" /></div>
          <div className="md:col-span-2"><Button onClick={handleSave} disabled={!canEdit || update.isPending} data-testid="save-settings">Save</Button></div>
        </CardContent>
      </Card>
    </div>
  )
}
