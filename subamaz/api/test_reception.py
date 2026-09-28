# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

PAYLOAD = {
	"customer_complaint": "AC not cooling",
	"terms_accepted": 1,
	"odometer_reading": 45000,
	"fuel_level": "Quarter",
	"damage_markers": [{"panel": "Rear Bumper", "damage_type": "Dent", "severity": "Moderate"}],
	"accessories": [{"accessory_name": "Floor Mats", "present": 1}],
	"personal_belongings": [{"belonging_name": "Laptop Bag", "notes": "On back seat"}],
	"photos": [
		{"photo": "/files/front.jpg", "photo_type": "Front"},
		{"photo": "/files/rear.jpg", "photo_type": "Rear"},
		{"photo": "/files/interior.jpg", "photo_type": "Interior"},
		{"photo": "/files/dashboard.jpg", "photo_type": "Dashboard"},
	],
}


class TestReceptionAPI(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"API Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"API-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"current_mileage": 20000,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "API",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		PAYLOAD["reception_advisor"] = self.employee.name

	def test_create_reception_denied_for_other_roles(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			self.assertRaises(
				frappe.PermissionError,
				self._call_create_reception,
			)
		finally:
			frappe.set_user("Administrator")

	def test_create_reception_creates_and_submits(self):
		user = self._create_user("Garage Reception")
		frappe.set_user(user)
		try:
			result = self._call_create_reception()
		finally:
			frappe.set_user("Administrator")
		name = result["name"]
		doc = frappe.get_doc("Vehicle Reception", name)
		self.assertEqual(doc.docstatus, 1)
		self.assertEqual(doc.customer_complaint, PAYLOAD["customer_complaint"])
		self.assertEqual(doc.damage_markers[0].panel, "Rear Bumper")
		self.assertEqual(doc.photos[0].photo_type, "Front")
		self.assertEqual(
			frappe.db.get_value("Garage Vehicle", self.vehicle.name, "current_status"), "Received"
		)

	def _call_create_reception(self):
		from subamaz.api.reception import create_reception

		return create_reception(self.vehicle.name, self.customer.name, frappe.as_json(PAYLOAD))

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.recapi@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role,
					"send_welcome_email": 0,
					"user_type": "System User",
					"roles": [{"role": role}],
				}
			)
			user.insert(ignore_permissions=True)
		return email
