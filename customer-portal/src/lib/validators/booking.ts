import { z } from "zod"

// Zod schema mirrors subamaz.api.booking.create_appointment_request validation
// Used with react-hook-form via zodResolver for any public booking React island
export const bookingSchema = z.object({
	customer_name: z.string().min(1, "Customer name is required").trim(),
	phone: z.string().min(1, "Phone is required").trim(),
	email: z.string().email("Invalid email").optional().or(z.literal("")),
	vehicle_registration: z.string().optional(),
	preferred_date: z.string().optional(),
	preferred_time: z.string().optional(),
	message: z.string().optional(),
})

export type BookingFormData = z.infer<typeof bookingSchema>

// Example RHF usage:
// const form = useForm<BookingFormData>({ resolver: zodResolver(bookingSchema), defaultValues: { customer_name: "", phone: "" } })
