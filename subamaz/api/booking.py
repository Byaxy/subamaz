# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def create_appointment_request(customer_name, phone, email=None, vehicle_registration=None, preferred_date=None, preferred_time=None, message=None):
	"""Guest booking: create Appointment Request draft.

	Validation mirrors Zod schema used on the frontend (react-hook-form+zod).
	"""
	if not customer_name or not customer_name.strip():
		frappe.throw(_("Customer name is required"))
	if not phone or not phone.strip():
		frappe.throw(_("Phone is required"))
	# light email check if provided
	if email and "@" not in email:
		frappe.throw(_("Invalid email"))

	doc = frappe.get_doc(
		{
			"doctype": "Appointment Request",
			"customer_name": customer_name.strip(),
			"phone": phone.strip(),
			"email": email.strip() if email else None,
			"vehicle_registration": vehicle_registration.strip() if vehicle_registration else None,
			"preferred_date": preferred_date or None,
			"preferred_time": preferred_time.strip() if preferred_time else None,
			"message": message.strip() if message else None,
			"status": "New",
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_appointment_requests(status=None):
	"""Reception helper: list bookings (for queue)."""
	filters = {}
	if status:
		filters["status"] = status
	return frappe.get_all("Appointment Request", filters=filters, fields=["name", "customer_name", "phone", "email", "vehicle_registration", "preferred_date", "preferred_time", "status", "linked_reception"], order_by="creation desc")


@frappe.whitelist()
def convert_appointment(appointment, vehicle=None, customer=None):
	"""Convert Appointment Request -> Vehicle Reception. Called from Desk/reception API."""
	appointment_doc = frappe.get_doc("Appointment Request", appointment)
	if appointment_doc.status == "Converted":
		frappe.throw(_("Already converted to {0}").format(appointment_doc.linked_reception))

	# minimal validation
	if not vehicle:
		# try to guess vehicle by registration if exists
		if appointment_doc.vehicle_registration:
			vehicle = frappe.db.get_value("Garage Vehicle", {"registration_number": appointment_doc.vehicle_registration}, "name")

	return {"appointment": appointment_doc.name, "status": appointment_doc.status}
