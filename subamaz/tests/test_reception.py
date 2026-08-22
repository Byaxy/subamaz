# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

PHOTO_TYPES = ("Front", "Rear", "Interior", "Dashboard")


class TestReceptionWorkflow(IntegrationTestCase):
	"""Cross-doctype reception workflow: intake flips the vehicle into the shop flow."""

	def test_full_intake_flips_vehicle_status_and_keeps_complaint(self):
		customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Flow Cust {frappe.generate_hash(length=4)}"}
		).insert()
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Flow",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Female",
				"date_of_birth": "1992-02-02",
				"date_of_joining": "2021-02-02",
			}
		).insert()
		vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"FL-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": customer.name,
			}
		).insert()

		reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": customer.name,
				"vehicle": vehicle.name,
				"reception_advisor": employee.name,
				"customer_complaint": "Squeals on cold starts",
				"terms_accepted": 1,
				"photos": [
					{"photo": f"/files/{t.lower()}.jpg", "photo_type": t} for t in PHOTO_TYPES
				],
			}
		).insert()
		reception.submit()

		self.assertEqual(reception.docstatus, 1)
		self.assertEqual(reception.status, "Submitted")
		self.assertEqual(
			frappe.db.get_value("Garage Vehicle", vehicle.name, "current_status"), "Received"
		)
		self.assertEqual(
			frappe.db.get_value("Vehicle Reception", reception.name, "customer_complaint"),
			"Squeals on cold starts",
		)
