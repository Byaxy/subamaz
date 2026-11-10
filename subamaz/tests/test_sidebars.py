# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.desk.doctype.custom_sidebar.custom_sidebar import get_customization

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
