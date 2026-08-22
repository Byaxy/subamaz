import frappe
from frappe import _
from frappe.model.document import Document


class VehicleReception(Document):
	def validate(self):
		self.validate_status()
		self.validate_vehicle_customer()
		if self.docstatus == 1:
			self.validate_terms()
			self.validate_required_photos()
		if self.get("amended_from"):
			self.validate_complaint_preserved()

	def validate_status(self):
		if self.docstatus == 1 and self.status != "Submitted":
			self.status = "Submitted"
		elif self.docstatus == 0 and self.status == "Submitted":
			frappe.throw(_("Status 'Submitted' can only be reached by submitting the document"))

	def validate_vehicle_customer(self):
		owner = frappe.db.get_value("Garage Vehicle", self.vehicle, "customer")
		if owner and owner != self.customer:
			frappe.throw(
				_("Vehicle {0} does not belong to customer {1}").format(self.vehicle, self.customer)
			)

	def validate_terms(self):
		if not self.terms_accepted:
			frappe.throw(_("Terms & Conditions must be accepted before submission"))

	def validate_required_photos(self):
		required = get_required_photo_types()
		present = {row.photo_type for row in self.photos or []}
		missing = [photo_type for photo_type in required if photo_type not in present]
		if missing:
			frappe.throw(
				_("Missing required arrival photos: {0}").format(", ".join(missing))
			)

	def validate_complaint_preserved(self):
		original = frappe.db.get_value("Vehicle Reception", self.amended_from, "customer_complaint")
		if (original or "") != (self.customer_complaint or ""):
			frappe.throw(_("Customer Complaint is preserved verbatim and cannot be amended"))

	def on_submit(self):
		frappe.db.set_value("Garage Vehicle", self.vehicle, "current_status", "Received")
		notify_advisors(self)


def get_required_photo_types():
	default = ("Front", "Rear", "Interior", "Dashboard")
	raw = frappe.db.get_single_value("Garage Settings", "reception_photo_requirements")
	if raw is None or not raw.strip():
		return list(default)
	return [photo_type.strip() for photo_type in raw.split(",") if photo_type.strip()]


def notify_advisors(reception):
	for user in frappe.get_all(
		"Has Role",
		filters={"role": "Garage Service Advisor", "parenttype": "User"},
		pluck="parent",
	):
		frappe.publish_realtime(
			"reception_submitted",
			{"reception": reception.name, "vehicle": reception.vehicle},
			user=user,
			after_commit=True,
		)
