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

	def test_get_vehicle_history(self):
		# Create employee as Administrator to avoid permission issues
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Hist",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert(ignore_permissions=True)
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import get_vehicle_history

			# Create a reception for history as Manager (has permission)
			reception = frappe.get_doc(
				{
					"doctype": "Vehicle Reception",
					"customer": self.customer.name,
					"vehicle": self.vehicle.name,
					"reception_advisor": employee.name,
					"customer_complaint": "History test",
					"terms_accepted": 1,
					"photos": [
						{"photo": "/files/front.jpg", "photo_type": "Front"},
						{"photo": "/files/rear.jpg", "photo_type": "Rear"},
						{"photo": "/files/interior.jpg", "photo_type": "Interior"},
						{"photo": "/files/dashboard.jpg", "photo_type": "Dashboard"},
					],
				}
			).insert()
			reception.submit()
			history = get_vehicle_history(self.vehicle.name)
			self.assertTrue(isinstance(history, list))
			self.assertTrue(any(h["doctype"] == "Vehicle Reception" for h in history))
			# Check order is chronological
			dates = [h["date"] for h in history]
			self.assertEqual(dates, sorted(dates))
		finally:
			frappe.set_user("Administrator")

	def test_get_stock_status_and_restock_preview(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import get_restock_preview, get_stock_status

			# Create a stock item with reorder level
			item = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": f"RSTK-{frappe.generate_hash(length=4)}",
					"item_name": "Restock Item",
					"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
					"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
					"is_stock_item": 1,
					"reorder_levels": [
						{
							"warehouse": frappe.db.get_value("Warehouse", {}, "name"),
							"warehouse_reorder_level": 10,
							"warehouse_reorder_qty": 20,
						}
					],
				}
			).insert(ignore_permissions=True)
			# Ensure Bin exists with low qty
			warehouse = frappe.db.get_value("Warehouse", {}, "name")
			# Create Bin via stock or direct
			if not frappe.db.exists("Bin", {"item_code": item.name, "warehouse": warehouse}):
				frappe.get_doc(
					{"doctype": "Bin", "item_code": item.name, "warehouse": warehouse, "actual_qty": 2}
				).insert(ignore_permissions=True)
			else:
				frappe.db.set_value("Bin", {"item_code": item.name, "warehouse": warehouse}, "actual_qty", 2)

			stock = get_stock_status(warehouse)
			self.assertTrue(isinstance(stock, list))

			preview = get_restock_preview(warehouse)
			self.assertIn("low_items", preview)
			self.assertIn("groups", preview)
			# Our item should be low
			found = any(i["item_code"] == item.name for i in preview["low_items"])
			self.assertTrue(found)
			# Groups by supplier — at least one group
			self.assertGreaterEqual(len(preview["groups"]), 1)
		finally:
			frappe.set_user("Administrator")

	def test_stock_capability_denied(self):
		# Technician has parts_stock, Reception does not (per ROLE_CEILING)
		user = self._create_user("Garage Reception")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import get_stock_status

			# Reception has no parts_stock, should be denied
			self.assertRaises(frappe.PermissionError, get_stock_status)
		finally:
			frappe.set_user("Administrator")

	def test_procurement_counts(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import get_procurement_counts

			counts = get_procurement_counts()
			self.assertIn("purchase_orders", counts)
			self.assertIn("supplier_quotations", counts)
		finally:
			frappe.set_user("Administrator")

	def test_procurement_capability_denied(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import get_procurement_counts

			self.assertRaises(frappe.PermissionError, get_procurement_counts)
		finally:
			frappe.set_user("Administrator")

	def test_money_counts_and_petty_cash(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import create_petty_cash, get_money_counts

			counts = get_money_counts()
			self.assertIn("invoices", counts)
			# Petty cash requires action:record_petty_cash
			res = create_petty_cash(amount=5000, description="Test petty", expense_type="Misc")
			self.assertIn("name", res)
			self.assertTrue(frappe.db.exists("Petty Cash Log", res["name"]))
		finally:
			frappe.set_user("Administrator")

	def test_money_capability_denied(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			from subamaz.api.admin import get_money_counts

			self.assertRaises(frappe.PermissionError, get_money_counts)
		finally:
			frappe.set_user("Administrator")

	def test_apply_discount_and_void_capability(self):
		# Manager has both, Service Advisor has discount but not void
		manager = self._create_user("Garage Manager")
		advisor = self._create_user("Garage Service Advisor")
		# Create invoice as Administrator
		company = frappe.db.get_value("Company", {}, "name")
		currency = frappe.db.get_value("Company", company, "default_currency") or "USD"
		customer = frappe.db.get_value("Customer", {}, "name")
		item = frappe.db.get_value("Item", {}, "item_code")
		inv = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"customer": customer,
				"company": company,
				"currency": currency,
				"conversion_rate": 1,
				"set_posting_time": 1,
				"posting_date": frappe.utils.today(),
				"due_date": frappe.utils.add_days(frappe.utils.today(), 10),
				"items": [{"item_code": item, "qty": 1, "rate": 1000, "conversion_rate": 1}],
			}
		)
		inv.insert(ignore_permissions=True)
		inv.submit()

		# Advisor can discount
		frappe.set_user(advisor)
		try:
			from subamaz.api.admin import apply_invoice_discount

			res = apply_invoice_discount(inv.name, "100")
			self.assertEqual(res["invoice"], inv.name)
		finally:
			frappe.set_user("Administrator")

		# Advisor cannot void
		frappe.set_user(advisor)
		try:
			from subamaz.api.admin import void_invoice

			self.assertRaises(frappe.PermissionError, void_invoice, inv.name)
		finally:
			frappe.set_user("Administrator")

		# Manager can void
		frappe.set_user(manager)
		try:
			from subamaz.api.admin import void_invoice

			res = void_invoice(inv.name)
			self.assertIn("status", res)
		finally:
			frappe.set_user("Administrator")
