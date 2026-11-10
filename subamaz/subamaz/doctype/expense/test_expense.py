# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.utils import today

from subamaz.subamaz.doctype.expense._test_helpers import ExpenseTestCase

IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Account",
	"Company",
	"Cost Center",
	"Mode of Payment",
	"Supplier",
	"Item",
	"Warehouse",
	"UOM",
	"Item Group",
	"Supplier Group",
	"Purchase Order",
	"Purchase Invoice",
	"Purchase Receipt",
	"Landed Cost Voucher",
	"Journal Entry",
	"Payment Entry",
]


class TestExpense(ExpenseTestCase):
	def test_naming_series(self):
		category = self.make_category(self.expense_account)
		doc = self.make_expense(expense_category=category.name).insert(ignore_permissions=True)
		self.assertRegex(doc.name, r"^EXP-\d{4}-\d{5}$")

	def test_amount_must_be_positive(self):
		category = self.make_category(self.expense_account)
		doc = self.make_expense(expense_category=category.name, amount=0)
		with self.assertRaisesRegex(frappe.ValidationError, "greater than zero"):
			doc.insert(ignore_permissions=True)

	def test_direct_payment_requires_category(self):
		doc = self.make_expense()
		with self.assertRaisesRegex(frappe.ValidationError, "Expense Category is required"):
			doc.insert(ignore_permissions=True)

	def test_direct_payment_creates_and_reverses_journal_entry(self):
		category = self.make_category(self.expense_account)
		doc = self.make_expense(expense_category=category.name).insert(ignore_permissions=True)
		doc.submit()

		self.assertTrue(doc.journal_entry)
		je = frappe.get_doc("Journal Entry", doc.journal_entry)
		self.assertEqual(je.docstatus, 1)
		rows = {row.account: row for row in je.accounts}
		self.assertEqual(rows[self.expense_account].debit_in_account_currency, 100)
		self.assertEqual(rows[self.cash_account].credit_in_account_currency, 100)

		doc.cancel()
		je.reload()
		self.assertEqual(je.docstatus, 2)

	def test_bank_payment_requires_reference(self):
		category = self.make_category(self.expense_account)
		mode = self.make_bank_mode()

		doc = self.make_expense(
			expense_category=category.name, mode_of_payment=mode.name
		)
		with self.assertRaisesRegex(frappe.ValidationError, "Reference No and Reference Date"):
			doc.insert(ignore_permissions=True)

		doc.reference_no = "BANK-001"
		doc.reference_date = today()
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.paid_from, self.bank_account)

	def test_non_accompanying_rejects_accompanying_category(self):
		category = self.make_category(self.valuation_account, accompanying=1)
		doc = self.make_expense(expense_category=category.name)
		with self.assertRaisesRegex(frappe.ValidationError, "Accompanying Expense Category"):
			doc.insert(ignore_permissions=True)

	def test_non_accompanying_rejects_valuation_account(self):
		category = self.make_category(self.valuation_account)
		doc = self.make_expense(expense_category=category.name)
		with self.assertRaisesRegex(frappe.ValidationError, "must not have Account Type"):
			doc.insert(ignore_permissions=True)

	def test_accompanying_requires_purchase_order(self):
		category = self.make_category(self.valuation_account, accompanying=1)
		doc = self.make_expense(expense_category=category.name, is_accompanying=1)
		with self.assertRaisesRegex(frappe.ValidationError, "At least one Purchase Order"):
			doc.insert(ignore_permissions=True)

	def test_accompanying_rejects_non_accompanying_category(self):
		category = self.make_category(self.expense_account)
		po = self.make_purchase_order()
		doc = self.make_expense(
			expense_category=category.name,
			is_accompanying=1,
			purchase_orders=[{"purchase_order": po.name}],
		)
		with self.assertRaisesRegex(frappe.ValidationError, "not marked as an Accompanying"):
			doc.insert(ignore_permissions=True)

	def test_accompanying_rejects_draft_purchase_order(self):
		category = self.make_category(self.valuation_account, accompanying=1)
		po = self.make_purchase_order(submit=False)
		doc = self.make_expense(
			expense_category=category.name,
			is_accompanying=1,
			purchase_orders=[{"purchase_order": po.name}],
		)
		with self.assertRaisesRegex(frappe.ValidationError, "must be submitted"):
			doc.insert(ignore_permissions=True)

	def test_accompanying_rejects_duplicate_purchase_orders(self):
		category = self.make_category(self.valuation_account, accompanying=1)
		po = self.make_purchase_order()
		doc = self.make_expense(
			expense_category=category.name,
			is_accompanying=1,
			purchase_orders=[{"purchase_order": po.name}, {"purchase_order": po.name}],
		)
		with self.assertRaisesRegex(frappe.ValidationError, "Duplicate Purchase Order"):
			doc.insert(ignore_permissions=True)

	def test_against_purchase_invoice_creates_and_reverses_payment_entry(self):
		pi = self.make_purchase_invoice()
		doc = self.make_expense(
			payment_type="Against Purchase Invoice",
			purchase_invoice=pi.name,
			amount=None,
		).insert(ignore_permissions=True)

		self.assertEqual(doc.amount, pi.outstanding_amount)
		doc.submit()
		self.assertTrue(doc.payment_entry)

		pe = frappe.get_doc("Payment Entry", doc.payment_entry)
		self.assertEqual(pe.docstatus, 1)
		self.assertEqual(pe.payment_type, "Pay")
		self.assertEqual(pe.references[0].reference_name, pi.name)

		doc.cancel()
		pe.reload()
		self.assertEqual(pe.docstatus, 2)

	def test_invoice_amount_cannot_exceed_outstanding(self):
		pi = self.make_purchase_invoice()
		doc = self.make_expense(
			payment_type="Against Purchase Invoice",
			purchase_invoice=pi.name,
			amount=pi.outstanding_amount + 1,
		)
		with self.assertRaisesRegex(frappe.ValidationError, "cannot exceed"):
			doc.insert(ignore_permissions=True)

	def test_cancelling_expense_without_lcv(self):
		category = self.make_category(self.expense_account)
		doc = self.make_expense(expense_category=category.name).insert(ignore_permissions=True)
		doc.submit()
		doc.cancel()
		self.assertEqual(doc.docstatus, 2)

	def test_permissions_matrix(self):
		roles = {row.role: row for row in frappe.get_meta("Expense").permissions}
		for role in ("System Manager", "Garage Accountant", "Garage Manager", "Accounts User"):
			self.assertTrue(roles[role].read and roles[role].write and roles[role].submit)
