import frappe
from frappe import _
from frappe.utils import has_common

ALLOWED_ROLES = ("Garage Reception", "Garage Supervisor", "Garage Manager")

TOP_LEVEL_FIELDS = (
	"reception_date",
	"reception_advisor",
	"appointment",
	"odometer_reading",
	"fuel_level",
	"battery_condition",
	"engine_starts",
	"vehicle_drivable",
	"customer_complaint",
	"customer_signature",
	"advisor_signature",
	"terms_accepted",
)

CHILD_TABLES = (
	"requested_services",
	"damage_markers",
	"accessories",
	"personal_belongings",
	"photos",
)


@frappe.whitelist(methods=["POST"])
def create_reception(vehicle, customer, payload):
	"""Create and submit a Vehicle Reception from an external client payload."""
	_gate_role()
	payload = _coerce_payload(payload)
	doc = frappe.new_doc("Vehicle Reception")
	doc.vehicle = vehicle
	doc.customer = customer
	for fieldname in TOP_LEVEL_FIELDS:
		if payload.get(fieldname) is not None:
			doc.set(fieldname, payload.get(fieldname))
	for table_fieldname in CHILD_TABLES:
		rows = payload.get(table_fieldname) or []
		doc.set(table_fieldname, _sanitize_rows(table_fieldname, rows))
	doc.insert()
	doc.submit()
	# handoff: if appointment linked, mark converted
	if doc.appointment:
		try:
			if frappe.db.exists("Appointment Request", doc.appointment):
				frappe.db.set_value(
					"Appointment Request",
					doc.appointment,
					{"status": "Converted", "linked_reception": doc.name},
				)
		except Exception:
			frappe.log_error(title="Appointment handoff failed", message=frappe.get_traceback())
	return {"name": doc.name}


def _gate_role():
	if not has_common(ALLOWED_ROLES, frappe.get_roles()):
		frappe.throw(_("You are not permitted to create vehicle receptions"), frappe.PermissionError)


def _coerce_payload(payload):
	if isinstance(payload, str):
		return frappe.parse_json(payload) or {}
	return payload or {}


def _sanitize_rows(table_fieldname, rows):
	child_doctype = frappe.get_meta("Vehicle Reception").get_field(table_fieldname).options
	valid_fieldnames = {field.fieldname for field in frappe.get_meta(child_doctype).fields}
	return [
		{key: value for key, value in row.items() if key in valid_fieldnames}
		for row in rows
	]
