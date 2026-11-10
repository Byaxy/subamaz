# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.subamaz.doctype.expense._test_helpers import ExpenseTestCase
from subamaz.subamaz.doctype.expense.landed_cost import (
	check_purchase_orders_fully_received,
	make_landed_cost_voucher,
)

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


class TestExpenseLandedCost(ExpenseTestCase):
	def _received_expense(self, receipts=(10,)):
		po = self.make_purchase_order(qty=sum(receipts))
		for qty in receipts:
			self.receive_purchase_order(po, qty)
		expense = self.make_accompanying_expense([po.name]).insert(ignore_permissions=True)
		expense.submit()
		return po, expense

	def test_partial_receipt_blocks_lcv(self):
		po = self.make_purchase_order(qty=10)
		self.receive_purchase_order(po, 4)
		expense = self.make_accompanying_expense([po.name]).insert(ignore_permissions=True)
		expense.submit()

		check = check_purchase_orders_fully_received([po.name])
		self.assertFalse(check["ready"])
		self.assertTrue(check["unreceived_items"])

		with self.assertRaisesRegex(frappe.ValidationError, "not fully received"):
			make_landed_cost_voucher(expense.name)

	def test_fully_received_returns_new_unsaved_lcv(self):
		po, expense = self._received_expense((4, 6))

		lcv = make_landed_cost_voucher(expense.name)
		self.assertFalse(lcv.name)
		self.assertEqual(lcv.docstatus, 0)
		self.assertEqual(lcv.company, self.company)
		self.assertEqual(len(lcv.purchase_receipts), 2)
		self.assertEqual(lcv.taxes[0].expense_account, self.valuation_account)
		self.assertEqual(lcv.taxes[0].amount, expense.amount)
		self.assertEqual(lcv.custom_expense, expense.name)
		self.assertEqual(lcv.custom_linked_purchase_order, po.name)
		self.assertIn(po.name, lcv.custom_linked_purchase_orders)

	def test_saving_lcv_links_expense_and_deleting_unlinks(self):
		_, expense = self._received_expense()
		lcv = make_landed_cost_voucher(expense.name).insert(ignore_permissions=True)

		expense.reload()
		self.assertEqual(expense.landed_cost_voucher, lcv.name)

		frappe.delete_doc("Landed Cost Voucher", lcv.name, ignore_permissions=True)
		expense.reload()
		self.assertFalse(expense.landed_cost_voucher)

	def test_duplicate_lcv_blocked(self):
		_, expense = self._received_expense()
		make_landed_cost_voucher(expense.name).insert(ignore_permissions=True)

		with self.assertRaisesRegex(frappe.ValidationError, "already exists"):
			make_landed_cost_voucher(expense.name)

	def test_non_accompanying_expense_cannot_make_lcv(self):
		category = self.make_category(self.expense_account)
		expense = self.make_expense(expense_category=category.name).insert(ignore_permissions=True)
		expense.submit()
		with self.assertRaisesRegex(frappe.ValidationError, "not marked as an accompanying"):
			make_landed_cost_voucher(expense.name)

	def test_unsubmitted_expense_cannot_make_lcv(self):
		po = self.make_purchase_order()
		expense = self.make_accompanying_expense([po.name]).insert(ignore_permissions=True)
		with self.assertRaisesRegex(frappe.ValidationError, "must be submitted"):
			make_landed_cost_voucher(expense.name)

	def test_cancelling_expense_deletes_draft_lcv(self):
		_, expense = self._received_expense()
		lcv = make_landed_cost_voucher(expense.name).insert(ignore_permissions=True)
		expense.reload()
		expense.cancel()

		self.assertFalse(frappe.db.exists("Landed Cost Voucher", lcv.name))

	def test_multiple_purchase_orders_are_all_included(self):
		po1 = self.make_purchase_order(qty=5)
		po2 = self.make_purchase_order(qty=5)
		self.receive_purchase_order(po1, 5)
		self.receive_purchase_order(po2, 5)
		expense = self.make_accompanying_expense([po1.name, po2.name]).insert(ignore_permissions=True)
		expense.submit()

		lcv = make_landed_cost_voucher(expense.name)
		self.assertEqual(len(lcv.purchase_receipts), 2)
		self.assertEqual(lcv.custom_linked_purchase_orders, f"{po1.name}, {po2.name}")

	def test_accompanying_invoice_category_mismatch_blocks_expense(self):
		po = self.make_purchase_order()
		pi = self.make_purchase_invoice(expense_account=self.expense_account)
		category = self.make_category(self.valuation_account, accompanying=1)
		expense = self.make_expense(
			payment_type="Against Purchase Invoice",
			purchase_invoice=pi.name,
			expense_category=category.name,
			is_accompanying=1,
			purchase_orders=[{"purchase_order": po.name}],
		)
		with self.assertRaisesRegex(frappe.ValidationError, "books its cost to"):
			expense.insert(ignore_permissions=True)
