# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

# tests create their own Customer; skipping keeps Frappe's generator
# out of the huge, drift-prone ERPNext/HRMS master-data graph
IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer", "Employee"]


class TestGarageVehicle(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Veh Cust {frappe.generate_hash(length=4)}"}
		).insert()

	def _make_vehicle(self, registration_number=None, vin=None, mileage=10000):
		suffix = frappe.generate_hash(length=5)
		return frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": registration_number or f"GV-{suffix}",
				"vin": vin or frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"current_mileage": mileage,
			}
		)

	def test_naming_series(self):
		doc = self._make_vehicle().insert()
		self.assertTrue(doc.name.startswith("GV-"))

	def test_registration_uniqueness(self):
		self._make_vehicle(registration_number="DUP-001").insert()
		duplicate = self._make_vehicle(registration_number="DUP-001")
		self.assertRaises(frappe.UniqueValidationError, duplicate.insert)

	def test_vin_uniqueness(self):
		self._make_vehicle(vin="VINX1234567890123").insert()
		duplicate = self._make_vehicle(vin="VINX1234567890123")
		self.assertRaises(frappe.UniqueValidationError, duplicate.insert)

	def test_search_fields(self):
		search_fields = [
			f.strip() for f in (frappe.get_meta("Garage Vehicle").search_fields or "").split(",")
		]
		for field in ("registration_number", "vin", "customer"):
			self.assertIn(field, search_fields)

	def test_mileage_guard_blocks_non_manager(self):
		doc = self._make_vehicle(mileage=10000).insert()
		user = self._create_user("Garage Reception")
		frappe.set_user(user)
		try:
			doc.current_mileage = 9000
			self.assertRaises(frappe.ValidationError, doc.save)
		finally:
			frappe.set_user("Administrator")

	def test_mileage_guard_allows_equal_or_higher(self):
		doc = self._make_vehicle(mileage=10000).insert()
		user = self._create_user("Garage Reception")
		frappe.set_user(user)
		try:
			doc.current_mileage = 12000
			doc.save()
			self.assertEqual(frappe.db.get_value("Garage Vehicle", doc.name, "current_mileage"), 12000)
		finally:
			frappe.set_user("Administrator")

	def test_mileage_guard_manager_override(self):
		doc = self._make_vehicle(mileage=10000).insert()
		manager = self._create_user("Garage Manager")
		frappe.set_user(manager)
		try:
			doc.current_mileage = 9000
			doc.save()
			self.assertEqual(frappe.db.get_value("Garage Vehicle", doc.name, "current_mileage"), 9000)
		finally:
			frappe.set_user("Administrator")

	def test_current_status_select_options(self):
		expected = [
			"Received",
			"Waiting Inspection",
			"Waiting Approval",
			"Waiting Parts",
			"Repairing",
			"Testing",
			"Ready",
			"Delivered",
			"Cancelled",
			"Available",
		]
		options = frappe.get_meta("Garage Vehicle").get_field("current_status").options.split("\n")
		self.assertEqual(options, expected)

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.veh@example.com"
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
