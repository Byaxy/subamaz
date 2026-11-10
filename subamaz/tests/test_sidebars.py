# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.desk.doctype.custom_sidebar.custom_sidebar import get_customization
from frappe.desk.doctype.dock.dock import resolve_app_dock

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestSidebars(SubamazTestCase):
	def test_expense_and_category_are_in_accounts_sidebar(self):
		self._assert_accounts_positions()

	def test_sync_keeps_accounts_sidebar_positions(self):
		from subamaz.sidebars import sync_accounts_sidebar

		sync_accounts_sidebar()
		sync_accounts_sidebar()
		self._assert_accounts_positions()

	def _assert_accounts_positions(self):
		layer = get_customization("Accounts", None)
		self.assertIsNotNone(layer)

		rows = list(layer.sidebar_items)
		positions = {(row.link_type, row.link_to): index for index, row in enumerate(rows)}

		self.assertEqual(positions[("DocType", "Expense")], positions[("DocType", "Payment Entry")] + 1)
		self.assertEqual(
			positions[("DocType", "Expense Category")],
			positions[("DocType", "Account Category")] + 1,
		)

	def test_expense_is_not_in_garage_sidebar(self):
		links = {
			(row.link_type, row.link_to)
			for row in frappe.get_doc("Sidebar", "Garage").items
		}
		self.assertNotIn(("DocType", "Expense"), links)
		self.assertNotIn(("DocType", "Expense Category"), links)

	def test_garage_dock_matches_erpnext_dock(self):
		def dock_rows(app):
			return [
				(row["link_type"], row["link_to"], row["title"], row["hidden"])
				for row in resolve_app_dock(app)
			]

		self.assertEqual(dock_rows("subamaz"), dock_rows("erpnext"))

		visible = {(row["link_type"], row["link_to"]) for row in resolve_app_dock("subamaz") if not row["hidden"]}
		for expected in [
			("Sidebar", "Setup"),
			("Sidebar", "Accounts"),
			("Sidebar", "Selling"),
			("Sidebar", "Buying"),
			("Sidebar", "Stock"),
			("Workspace", "Garage"),
			("Sidebar", "Projects"),
			("Sidebar", "Assets"),
			("Sidebar", "Portal"),
		]:
			self.assertIn(expected, visible)

	def test_garage_sidebar_has_no_generic_groups(self):
		doc = frappe.get_doc("Sidebar", "Garage")
		labels = {row.label for row in doc.items if row.type == "Section Break"}
		self.assertFalse(labels & {"Sales", "Purchases", "Accounting", "Stock & Parts"})

		links = {(row.link_type, row.link_to) for row in doc.items}
		for removed in [
			("DocType", "Customer"),
			("DocType", "Quotation"),
			("DocType", "Sales Order"),
			("DocType", "Sales Invoice"),
			("DocType", "Supplier"),
			("DocType", "Purchase Order"),
			("DocType", "Purchase Invoice"),
			("DocType", "Payment Entry"),
			("DocType", "Journal Entry"),
			("DocType", "Item"),
			("DocType", "Stock Entry"),
		]:
			self.assertNotIn(removed, links)

	def test_garage_sidebar_keeps_garage_groups(self):
		doc = frappe.get_doc("Sidebar", "Garage")
		labels = {row.label for row in doc.items if row.type == "Section Break"}
		self.assertTrue({"Operations", "Projects", "Reports", "Setup"} <= labels)

		links = {(row.link_type, row.link_to) for row in doc.items}
		for kept in [
			("DocType", "Garage Vehicle"),
			("DocType", "Repair Task"),
			("DocType", "Garage Settings"),
			("DocType", "Theme"),
		]:
			self.assertIn(kept, links)
