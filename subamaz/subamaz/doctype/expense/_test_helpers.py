# Copyright (c) 2026, SubaMaz Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class ExpenseTestCase(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.company = (
			"_Test Company" if frappe.db.exists("Company", "_Test Company") else frappe.db.get_value(
				"Company", {}, "name"
			)
		)
		self.currency = frappe.db.get_value("Company", self.company, "default_currency")
		self.expense_account = self._account("Expense Account")
		self.valuation_account = self._account("Expenses Included In Valuation")
		self.cash_account = self._account("Cash")
		self.bank_account = self._account("Bank")
		self.cost_center = frappe.db.get_value(
			"Cost Center", {"company": self.company, "is_group": 0}, "name"
		)
		self.warehouse = (
			"_Test Warehouse - _TC"
			if frappe.db.exists("Warehouse", "_Test Warehouse - _TC")
			else frappe.db.get_value(
				"Warehouse", {"company": self.company, "is_group": 0}, "name"
			)
		)
		self._ensure_cash_mode()

	def _account(self, account_type):
		return frappe.db.get_value(
			"Account",
			{"company": self.company, "account_type": account_type, "is_group": 0},
			"name",
		)

	def _ensure_cash_mode(self):
		mop = frappe.get_doc("Mode of Payment", "Cash")
		row = next((row for row in mop.accounts if row.company == self.company), None)
		if row:
			self.cash_account = row.default_account
			return
		mop.append("accounts", {"company": self.company, "default_account": self.cash_account})
		mop.save(ignore_permissions=True)

	def make_category(self, account, accompanying=0):
		name = f"_Test Expense Category {frappe.generate_hash(length=8)}"
		return frappe.get_doc(
			{
				"doctype": "Expense Category",
				"category_name": name,
				"expense_account": account,
				"is_accompanying_expense": accompanying,
			}
		).insert(ignore_permissions=True)

	def make_supplier(self):
		return frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": f"_Test Expense Supplier {frappe.generate_hash(length=8)}",
				"supplier_group": frappe.db.get_value("Supplier Group", {"is_group": 0}, "name"),
			}
		).insert(ignore_permissions=True)

	def make_item(self, stock_item=1):
		return frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"_Test Expense Item {frappe.generate_hash(length=8)}",
				"item_name": "Expense Test Item",
				"item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
				"stock_uom": "Nos",
				"is_stock_item": stock_item,
			}
		).insert(ignore_permissions=True)

	def make_purchase_order(self, qty=10, submit=True):
		supplier = self.make_supplier()
		item = self.make_item()
		po = frappe.new_doc("Purchase Order")
		po.company = self.company
		po.supplier = supplier.name
		po.transaction_date = today()
		po.schedule_date = today()
		po.currency = self.currency
		po.conversion_rate = 1
		po.price_list_currency = self.currency
		po.plc_conversion_rate = 1
		po.append(
			"items",
			{
				"item_code": item.name,
				"schedule_date": today(),
				"qty": qty,
				"rate": 100,
				"warehouse": self.warehouse,
				"cost_center": self.cost_center,
			},
		)
		po.insert(ignore_permissions=True)
		return po.submit() if submit else po

	def receive_purchase_order(self, po, qty):
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

		pr = make_purchase_receipt(po.name)
		pr.items[0].qty = qty
		pr.items[0].received_qty = qty
		return pr.insert(ignore_permissions=True).submit()

	def make_purchase_invoice(self, expense_account=None):
		supplier = self.make_supplier()
		item = self.make_item(stock_item=0)
		pi = frappe.new_doc("Purchase Invoice")
		pi.company = self.company
		pi.supplier = supplier.name
		pi.posting_date = today()
		pi.set_posting_time = 1
		pi.currency = self.currency
		pi.conversion_rate = 1
		pi.price_list_currency = self.currency
		pi.plc_conversion_rate = 1
		pi.append(
			"items",
			{
				"item_code": item.name,
				"qty": 1,
				"rate": 100,
				"expense_account": expense_account or self.expense_account,
				"cost_center": self.cost_center,
			},
		)
		return pi.insert(ignore_permissions=True).submit()

	def make_expense(self, **overrides):
		args = {
			"doctype": "Expense",
			"company": self.company,
			"expense_date": today(),
			"expense_description": "Test Expense",
			"amount": 100,
			"payee": "Test Payee",
			"payment_type": "Direct Payment",
			"mode_of_payment": "Cash",
		}
		args.update(overrides)
		return frappe.get_doc(args)

	def make_accompanying_expense(self, po_names, **overrides):
		category = overrides.pop("category", None) or self.make_category(
			self.valuation_account, accompanying=1
		)
		args = {
			"expense_category": category.name,
			"is_accompanying": 1,
			"purchase_orders": [{"purchase_order": po} for po in po_names],
		}
		args.update(overrides)
		return self.make_expense(**args)

	def make_bank_mode(self):
		mode = frappe.get_doc(
			{
				"doctype": "Mode of Payment",
				"mode_of_payment": f"_Test Expense Bank {frappe.generate_hash(length=8)}",
				"enabled": 1,
			}
		)
		mode.append("accounts", {"company": self.company, "default_account": self.bank_account})
		return mode.insert(ignore_permissions=True)
