# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestAdminSearch(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"AdminSearch Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"AS-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.admin_{frappe.generate_hash(length=4)}@example.com"
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

	def test_global_search_returns_typed_results(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import global_search

			results = global_search(self.vehicle.registration_number[:4])
			self.assertTrue(isinstance(results, list))
			# should contain at least the vehicle
			found = any(r["doctype"] == "Garage Vehicle" and r["name"] == self.vehicle.name for r in results)
			self.assertTrue(found)
			# result shape
			for r in results:
				self.assertIn("doctype", r)
				self.assertIn("name", r)
				self.assertIn("label", r)
				self.assertIn("route", r)
		finally:
			frappe.set_user("Administrator")

	def test_global_search_empty_query(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import global_search

			self.assertEqual(global_search(""), [])
			self.assertEqual(global_search("   "), [])
		finally:
			frappe.set_user("Administrator")

	def test_global_search_guest_denied(self):
		frappe.set_user("Guest")
		try:
			from subamaz.api.admin import global_search

			self.assertRaises(frappe.PermissionError, global_search, "test")
		finally:
			frappe.set_user("Administrator")
