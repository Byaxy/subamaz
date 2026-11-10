# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.subamaz.doctype.expense._test_helpers import ExpenseTestCase

IGNORE_TEST_RECORD_DEPENDENCIES = ["Account", "Company", "Cost Center", "Mode of Payment"]


class TestExpenseCategory(ExpenseTestCase):
	def test_naming_by_category_name(self):
		category = self.make_category(self.expense_account)
		self.assertEqual(category.name, category.category_name)

	def test_accompanying_requires_valuation_account(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_category(self.expense_account, accompanying=1)

	def test_accompanying_accepts_valuation_account(self):
		category = self.make_category(self.valuation_account, accompanying=1)
		self.assertTrue(category.is_accompanying_expense)

	def test_non_accompanying_accepts_expense_account(self):
		category = self.make_category(self.expense_account)
		self.assertFalse(category.is_accompanying_expense)

	def test_permissions_matrix(self):
		roles = {row.role: row for row in frappe.get_meta("Expense Category").permissions}
		for role in ("System Manager", "Garage Accountant", "Garage Manager", "Accounts User"):
			self.assertTrue(roles[role].read and roles[role].write and roles[role].create)
