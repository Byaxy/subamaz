import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { useState } from "react"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useCreateReception, useCustomers, useVehicles, useEmployees } from "@/lib/queries/service"
import { toast } from "sonner"

export const Route = createFileRoute("/service/reception/new")({
  component: WalkaroundPage,
  validateSearch: (search: Record<string, unknown>) => ({ resume: search.resume as string | undefined }),
})

const PANELS = ["Front Bumper", "Rear Bumper", "Hood", "Roof", "Left Fender", "Right Fender", "Left Door Front", "Left Door Rear", "Right Door Front", "Right Door Rear", "Trunk", "Windshield", "Rear Glass"] as const
const DAMAGE_TYPES = ["Scratch", "Dent", "Crack", "Missing Part", "Paint Damage", "Rust", "Broken Glass"] as const
const SEVERITIES = ["Minor", "Moderate", "Severe"] as const
const ACCESSORIES = ["Spare Tire", "Jack", "Wheel Spanner", "Floor Mats", "Fire Extinguisher", "Radio", "Dash Camera", "First Aid Kit", "Tool Kit", "Tow Hook", "Service Book", "Registration Documents", "Other"] as const
const BELONGINGS = ["Laptop Bag", "Child Seat", "Umbrella", "Mobile Charger", "Cash (Declared)", "Documents", "Other"] as const
const MANDATORY_PHOTOS = ["Front", "Rear", "Interior", "Dashboard"]
const PHOTO_TYPES = ["Front", "Rear", "Left Side", "Right Side", "Interior", "Dashboard", "Engine Bay", "Damage Close-up", "Before", "During", "After"] as const

type DamageMarker = { panel: string; damage_type: string; severity: string; notes?: string }
type PhotoRow = { photo: string; photo_type: string; taken_on?: string; notes?: string }

// Zod schema outside component for resolver caching (valid-resolver-caching)
const receptionSchema = z.object({
  customer: z.string().min(1, "Customer required"),
  vehicle: z.string().min(1, "Vehicle required"),
  reception_advisor: z.string().min(1, "Advisor required"),
  odometer_reading: z.coerce.number().int().optional(),
  fuel_level: z.enum(["Empty", "Quarter", "Half", "Three Quarter", "Full"]).default("Half"),
  battery_condition: z.enum(["Good", "Weak", "Dead", "Not Checked"]).default("Good"),
  engine_starts: z.boolean().default(true),
  vehicle_drivable: z.boolean().default(true),
  customer_complaint: z.string().optional(),
  terms_accepted: z.boolean().refine((v) => v === true, { message: "Terms must be accepted" }),
})

type ReceptionForm = z.infer<typeof receptionSchema>

function VehicleSilhouette({ onSelect }: { onSelect: (panel: string) => void }) {
  return (
    <div className="border rounded p-4 bg-muted/20" data-testid="vehicle-silhouette">
      <p className="text-sm font-medium mb-2">Tap a panel to add damage</p>
      <div className="grid grid-cols-3 gap-2">
        {PANELS.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => onSelect(p)}
            className="border rounded p-2 text-xs hover:bg-[var(--app-select-row-hover-bg)]"
            data-testid={`panel-${p}`}
          >
            {p}
          </button>
        ))}
      </div>
      <svg viewBox="0 0 200 100" className="w-full h-24 mt-4 opacity-20">
        <rect x="10" y="20" width="180" height="60" rx="10" fill="currentColor" />
        <circle cx="50" cy="80" r="10" fill="currentColor" />
        <circle cx="150" cy="80" r="10" fill="currentColor" />
      </svg>
    </div>
  )
}

function WalkaroundPage() {
  const navigate = useNavigate()
  const search = useSearch({ from: "/service/reception/new" })
  const [step, setStep] = useState(1)
  const [customerSearch, setCustomerSearch] = useState("")
  const [vehicleSearch, setVehicleSearch] = useState("")
  const [damageMarkers, setDamageMarkers] = useState<DamageMarker[]>([])
  const [pendingPanel, setPendingPanel] = useState<string | null>(null)
  const [pendingDamage, setPendingDamage] = useState<DamageMarker>({ panel: "", damage_type: "Scratch", severity: "Minor" })
  const [photos, setPhotos] = useState<PhotoRow[]>([])
  const [accessories, setAccessories] = useState<Record<string, boolean>>({})
  const [belongings, setBelongings] = useState<Record<string, boolean>>({})
  const [customerSig, setCustomerSig] = useState("")
  const [advisorSig, setAdvisorSig] = useState("")

  const customers = useCustomers(customerSearch)
  const vehicles = useVehicles(vehicleSearch)
  const employees = useEmployees()
  const create = useCreateReception()

  const form = useForm<ReceptionForm>({
    resolver: zodResolver(receptionSchema),
    defaultValues: {
      customer: search.resume ? "" : "",
      vehicle: "",
      reception_advisor: "",
      fuel_level: "Half",
      battery_condition: "Good",
      engine_starts: true,
      vehicle_drivable: true,
      customer_complaint: "",
      terms_accepted: false,
    },
    mode: "onSubmit",
    reValidateMode: "onBlur",
  })

  const { control, handleSubmit, watch, setValue, formState } = form
  const watchedCustomer = watch("customer")
  const watchedVehicle = watch("vehicle")
  const watchedAdvisor = watch("reception_advisor")
  const watchedTerms = watch("terms_accepted")

  const mandatoryOk = MANDATORY_PHOTOS.every((t) => photos.some((p) => p.photo_type === t))
  const canSubmit = watchedTerms && mandatoryOk && watchedCustomer && watchedVehicle && watchedAdvisor

  const addDamage = () => {
    if (!pendingPanel) return
    setDamageMarkers([...damageMarkers, { ...pendingDamage, panel: pendingPanel }])
    setPendingPanel(null)
    setPendingDamage({ panel: "", damage_type: "Scratch", severity: "Minor" })
  }

  const handlePhoto = (e: React.ChangeEvent<HTMLInputElement>, type: string) => {
    const file = e.target.files?.[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    setPhotos([...photos, { photo: url, photo_type: type, taken_on: new Date().toISOString() }])
  }

  const onSubmit = handleSubmit(async (data) => {
    try {
      const payload: any = {
        reception_advisor: data.reception_advisor,
        odometer_reading: data.odometer_reading,
        fuel_level: data.fuel_level,
        battery_condition: data.battery_condition,
        engine_starts: data.engine_starts ? 1 : 0,
        vehicle_drivable: data.vehicle_drivable ? 1 : 0,
        customer_complaint: data.customer_complaint,
        terms_accepted: data.terms_accepted ? 1 : 0,
        customer_signature: customerSig,
        advisor_signature: advisorSig,
        damage_markers: damageMarkers,
        accessories: Object.entries(accessories)
          .filter(([, v]) => v)
          .map(([k]) => ({ accessory_name: k, present: 1 })),
        personal_belongings: Object.entries(belongings)
          .filter(([, v]) => v)
          .map(([k]) => ({ belonging_name: k, present: 1 })),
        photos: photos.map((p) => ({ photo: p.photo, photo_type: p.photo_type, taken_on: p.taken_on })),
      }
      const res: any = await create.mutateAsync({ vehicle: data.vehicle, customer: data.customer, payload })
      toast.success(`Reception ${res.name} created`)
      navigate({ to: "/service/receptions" })
    } catch (err: any) {
      toast.error(err?.message || "Create failed")
    }
  })

  const handlePark = async () => {
    const data = form.getValues()
    try {
      const { db } = await import("@/lib/frappe-client")
      const doc: any = await db.createDoc("Vehicle Reception", {
        customer: data.customer,
        vehicle: data.vehicle,
        reception_advisor: data.reception_advisor,
        status: "Draft — Parked",
        customer_complaint: data.customer_complaint,
        damage_markers: damageMarkers,
        photos,
      } as any)
      toast.success(`Parked ${doc.name}`)
      navigate({ to: "/service/receptions/queue" })
    } catch (err: any) {
      toast.error(err?.message || "Park failed")
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4" data-testid="walkaround">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">New Reception — Walkaround</h1>
        <span className="text-sm text-muted-foreground">Step {step} / 5</span>
      </div>

      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((s) => (
          <div key={s} className={`h-1 flex-1 rounded ${s <= step ? "bg-[var(--app-primary)]" : "bg-muted"}`} />
        ))}
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        {step === 1 && (
          <Card data-testid="step-1">
            <CardHeader>
              <CardTitle>Customer + Vehicle</CardTitle>
              <CardDescription>Search or register — validated with Zod</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div>
                <Label>Customer search</Label>
                <Input value={customerSearch} onChange={(e) => setCustomerSearch(e.target.value)} placeholder="Type name" data-testid="customer-search" />
                <div className="mt-2 flex flex-col gap-1 max-h-32 overflow-auto">
                  {(customers.data || []).map((c: any) => (
                    <button
                      key={c.name}
                      type="button"
                      onClick={() => setValue("customer", c.name, { shouldValidate: true })}
                      className={`text-left p-1 border rounded ${watchedCustomer === c.name ? "bg-accent" : ""}`}
                      data-testid={`customer-${c.name}`}
                    >
                      {c.customer_name} ({c.name})
                    </button>
                  ))}
                </div>
                <Controller
                  control={control}
                  name="customer"
                  render={({ field, fieldState }) => (
                    <div>
                      <Input {...field} placeholder="Selected customer" className="mt-2" data-testid="customer-selected" aria-invalid={!!fieldState.error} />
                      {fieldState.error && <p className="text-xs text-destructive">{fieldState.error.message}</p>}
                    </div>
                  )}
                />
              </div>
              <div>
                <Label>Vehicle search (registration)</Label>
                <Input value={vehicleSearch} onChange={(e) => setVehicleSearch(e.target.value)} placeholder="Type registration" data-testid="vehicle-search" />
                <div className="mt-2 flex flex-col gap-1 max-h-32 overflow-auto">
                  {(vehicles.data || []).map((v: any) => (
                    <button
                      key={v.name}
                      type="button"
                      onClick={() => setValue("vehicle", v.name, { shouldValidate: true })}
                      className={`text-left p-1 border rounded ${watchedVehicle === v.name ? "bg-accent" : ""}`}
                      data-testid={`vehicle-${v.name}`}
                    >
                      {v.registration_number} — {v.vin}
                    </button>
                  ))}
                </div>
                <Controller
                  control={control}
                  name="vehicle"
                  render={({ field, fieldState }) => (
                    <div>
                      <Input {...field} placeholder="Selected vehicle" className="mt-2" data-testid="vehicle-selected" aria-invalid={!!fieldState.error} />
                      {fieldState.error && <p className="text-xs text-destructive">{fieldState.error.message}</p>}
                    </div>
                  )}
                />
              </div>
              <div>
                <Label>Reception Advisor (Employee)</Label>
                <Controller
                  control={control}
                  name="reception_advisor"
                  render={({ field, fieldState }) => (
                    <div>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger data-testid="advisor-select" aria-invalid={!!fieldState.error}>
                          <SelectValue placeholder="Select advisor" />
                        </SelectTrigger>
                        <SelectContent>
                          {(employees.data || []).map((e: any) => (
                            <SelectItem key={e.name} value={e.name}>
                              {e.employee_name || e.first_name} ({e.name})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {fieldState.error && <p className="text-xs text-destructive">{fieldState.error.message}</p>}
                    </div>
                  )}
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label>Odometer</Label>
                  <Controller
                    control={control}
                    name="odometer_reading"
                    render={({ field }) => (
                      <Input type="number" value={field.value ?? ""} onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)} data-testid="odometer" />
                    )}
                  />
                </div>
                <div>
                  <Label>Fuel</Label>
                  <Controller
                    control={control}
                    name="fuel_level"
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {["Empty", "Quarter", "Half", "Three Quarter", "Full"].map((f) => (
                            <SelectItem key={f} value={f}>
                              {f}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <div>
                  <Label>Battery</Label>
                  <Controller
                    control={control}
                    name="battery_condition"
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {["Good", "Weak", "Dead", "Not Checked"].map((b) => (
                            <SelectItem key={b} value={b}>
                              {b}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                <Controller
                  control={control}
                  name="engine_starts"
                  render={({ field }) => (
                    <label className="flex items-center gap-2 mt-6">
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} data-testid="engine-starts" />
                      <span className="text-sm">Engine Starts</span>
                    </label>
                  )}
                />
                <Controller
                  control={control}
                  name="vehicle_drivable"
                  render={({ field }) => (
                    <label className="flex items-center gap-2">
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} data-testid="drivable" />
                      <span className="text-sm">Drivable</span>
                    </label>
                  )}
                />
              </div>
              <div>
                <Label>Complaint (verbatim)</Label>
                <Controller control={control} name="customer_complaint" render={({ field }) => <Textarea {...field} data-testid="complaint" />} />
              </div>
              {Object.keys(formState.errors).length > 0 && <div className="text-xs text-destructive">Fix validation errors before next</div>}
            </CardContent>
          </Card>
        )}

        {step === 2 && (
          <Card data-testid="step-2">
            <CardHeader>
              <CardTitle>Damage Markers</CardTitle>
              <CardDescription>Tap silhouette, fill form</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <VehicleSilhouette onSelect={setPendingPanel} />
              {pendingPanel && (
                <div className="border p-3 rounded flex flex-col gap-2" data-testid="damage-form">
                  <div>Panel: {pendingPanel}</div>
                  <Select value={pendingDamage.damage_type} onValueChange={(v) => setPendingDamage({ ...pendingDamage, damage_type: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DAMAGE_TYPES.map((d) => (
                        <SelectItem key={d} value={d}>
                          {d}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={pendingDamage.severity} onValueChange={(v) => setPendingDamage({ ...pendingDamage, severity: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SEVERITIES.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button type="button" onClick={addDamage} data-testid="add-damage">
                    Add marker
                  </Button>
                </div>
              )}
              <div className="text-sm" data-testid="damage-count">
                Markers: {damageMarkers.length}
              </div>
              {damageMarkers.map((m, i) => (
                <div key={i} className="text-xs border p-1 rounded">
                  {m.panel} — {m.damage_type} ({m.severity})
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {step === 3 && (
          <Card data-testid="step-3">
            <CardHeader>
              <CardTitle>Photos</CardTitle>
              <CardDescription>Camera capture — mandatory: {MANDATORY_PHOTOS.join(", ")}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {PHOTO_TYPES.map((t) => (
                <div key={t} className="flex items-center gap-2">
                  <span className="w-32 text-sm">
                    {t} {MANDATORY_PHOTOS.includes(t) && "*"}
                  </span>
                  <Input type="file" accept="image/*" capture={t === "Front" ? "environment" : undefined} onChange={(e) => handlePhoto(e, t)} data-testid={`photo-${t}`} />
                  <span className="text-xs">{photos.filter((p) => p.photo_type === t).length} </span>
                </div>
              ))}
              <div className="text-sm" data-testid="photo-count">
                Photos: {photos.length} / mandatory {MANDATORY_PHOTOS.filter((m) => photos.some((p) => p.photo_type === m)).length}/{MANDATORY_PHOTOS.length}
              </div>
              {!mandatoryOk && <div className="text-xs text-destructive">Need all mandatory photos before submit</div>}
            </CardContent>
          </Card>
        )}

        {step === 4 && (
          <Card data-testid="step-4">
            <CardHeader>
              <CardTitle>Accessories + Belongings</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-sm mb-2">Accessories</h4>
                {ACCESSORIES.map((a) => (
                  <label key={a} className="flex items-center gap-2 text-sm">
                    <Checkbox checked={!!accessories[a]} onCheckedChange={(v) => setAccessories({ ...accessories, [a]: !!v })} data-testid={`acc-${a}`} />
                    {a}
                  </label>
                ))}
              </div>
              <div>
                <h4 className="font-medium text-sm mb-2">Belongings</h4>
                {BELONGINGS.map((b) => (
                  <label key={b} className="flex items-center gap-2 text-sm">
                    <Checkbox checked={!!belongings[b]} onCheckedChange={(v) => setBelongings({ ...belongings, [b]: !!v })} data-testid={`bel-${b}`} />
                    {b}
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {step === 5 && (
          <Card data-testid="step-5">
            <CardHeader>
              <CardTitle>Terms + Signatures</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Controller
                control={control}
                name="terms_accepted"
                render={({ field, fieldState }) => (
                  <div>
                    <label className="flex items-center gap-2">
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} data-testid="terms" aria-invalid={!!fieldState.error} />
                      <span className="text-sm">Terms & Conditions Accepted *</span>
                    </label>
                    {fieldState.error && <p className="text-xs text-destructive">{fieldState.error.message}</p>}
                  </div>
                )}
              />
              <div>
                <Label>Customer Signature (file)</Label>
                <Input type="file" accept="image/*" onChange={(e) => setCustomerSig(e.target.files?.[0] ? URL.createObjectURL(e.target.files[0]) : "")} data-testid="cust-sig" />
              </div>
              <div>
                <Label>Advisor Signature (file)</Label>
                <Input type="file" accept="image/*" onChange={(e) => setAdvisorSig(e.target.files?.[0] ? URL.createObjectURL(e.target.files[0]) : "")} data-testid="adv-sig" />
              </div>
              {!canSubmit && <div className="text-xs text-destructive">Need terms + mandatory photos + customer/vehicle/advisor</div>}
            </CardContent>
          </Card>
        )}

        <div className="flex justify-between">
          <Button type="button" variant="outline" onClick={() => setStep(Math.max(1, step - 1))} disabled={step === 1}>
            Back
          </Button>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={handlePark} data-testid="park">
              Park
            </Button>
            {step < 5 ? (
              <Button type="button" onClick={() => setStep(step + 1)} data-testid="next">
                Next
              </Button>
            ) : (
              <Button type="submit" disabled={!canSubmit || create.isPending} data-testid="submit-reception">
                {create.isPending ? "Submitting..." : "Submit Reception"}
              </Button>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}
