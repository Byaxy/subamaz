# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.model.document import Document


class VehicleInspection(Document):
	def validate(self):
		self._set_customer_from_vehicle()

	def _set_customer_from_vehicle(self):
		if self.customer:
			return
		if not self.vehicle:
			return
		customer = frappe.db.get_value("Garage Vehicle", self.vehicle, "customer")
		if customer:
			self.customer = customer

	def on_submit(self):
		self._send_inspection_email()
		self._push_service_timeline()

	def get_pdf(self):
		html = frappe.get_print(
			self.doctype, self.name, "Vehicle Inspection Report", as_pdf=False
		)
		try:
			from frappe.utils.pdf import get_pdf

			return get_pdf(html)
		except Exception:
			frappe.log_error(
				title="Vehicle Inspection PDF failed",
				message=frappe.get_traceback(),
			)
			return None

	def _send_inspection_email(self):
		contact_name = frappe.db.get_value(
			"Dynamic Link",
			{
				"link_doctype": "Customer",
				"link_name": self.customer,
				"parenttype": "Contact",
			},
			"parent",
		)
		if not contact_name:
			frappe.logger().info(f"No contact for customer {self.customer}; skipping inspection email")
			return
		email = frappe.db.get_value("Contact", contact_name, "email_id")
		if not email:
			email = frappe.db.get_value(
				"Contact Email", {"parent": contact_name, "is_primary": 1}, "email_id"
			) or frappe.db.get_value("Contact Email", {"parent": contact_name}, "email_id")
		if not email:
			frappe.logger().info(f"Contact {contact_name} has no email_id; skipping inspection email")
			return
		pdf_content = None
		try:
			pdf_content = self.get_pdf()
		except Exception:
			frappe.log_error(title="Vehicle Inspection PDF for email failed", message=frappe.get_traceback())
		attachments = None
		if pdf_content:
			attachments = [{"fname": f"{self.name}.pdf", "fcontent": pdf_content}]
		frappe.sendmail(
			recipients=[email],
			subject=f"Inspection Report {self.name} — {self.vehicle}",
			message=(
				f"Inspection Result: {self.inspection_result or 'N/A'}<br>"
				f"Recommendation: {self.recommendation or 'N/A'}<br>"
				f"Notes: {self.notes or ''}"
			),
			attachments=attachments,
			reference_doctype=self.doctype,
			reference_name=self.name,
		)

	def _push_service_timeline(self):
		if not self.vehicle:
			return
		if not frappe.db.exists("DocType", "Service Timeline Entry"):
			return
		if not frappe.db.exists("DocType", "Service Order"):
			return
		service_order = frappe.db.get_value("Garage Vehicle", self.vehicle, "current_service_order")
		if not service_order:
			return
		if not frappe.db.exists("Service Order", service_order):
			return
		description = f"Inspection {self.name}: {self.inspection_result or 'N/A'} — {self.recommendation or 'N/A'}"
		try:
			doc = frappe.get_doc("Service Order", service_order)
			doc.append(
				"timeline",
				{
					"event_type": "System",
					"description": description,
					"visible_to_customer": 1,
					"user": frappe.session.user,
				},
			)
			doc.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(title="Vehicle Inspection timeline push failed", message=frappe.get_traceback())
