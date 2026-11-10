# Copyright (c) 2026, SubaMaz Contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from subamaz.subamaz.doctype.expense import accounts, landed_cost

VALUATION_ACCOUNT_TYPE = "Expenses Included In Valuation"


class Expense(Document):
	def validate(self):
		accounts.set_company_defaults(self)
		accounts.resolve_payment_account(self)
		accounts.resolve_paid_to(self)
		accounts.set_account_currencies(self)
		self._validate_category_required()
		self._validate_invoice_link()
		self._validate_accompanying()
		self._validate_amount()
		self._validate_reference()
		accounts.validate_paid_from(self)
		accounts.validate_paid_to(self)
		accounts.validate_single_currency(self)

	def on_submit(self):
		if self.payment_type == "Direct Payment":
			accounts.create_journal_entry(self)
		else:
			accounts.create_payment_entry(self)

	def on_cancel(self):
		landed_cost.cancel_linked_lcv(self)
		if self.payment_type == "Direct Payment":
			accounts.reverse_journal_entry(self)
		else:
			accounts.reverse_payment_entry(self)

	def _validate_category_required(self):
		if (self.payment_type == "Direct Payment" or self.is_accompanying) and not self.expense_category:
			frappe.throw(_("Expense Category is required."))

	def _validate_invoice_link(self):
		if self.payment_type != "Against Purchase Invoice":
			self.purchase_invoice = None
			return
		if not self.purchase_invoice:
			frappe.throw(_("Purchase Invoice is required for Against Purchase Invoice payment type."))

		pi = frappe.db.get_value(
			"Purchase Invoice",
			self.purchase_invoice,
			["docstatus", "outstanding_amount", "company", "supplier"],
			as_dict=True,
		)
		if not pi:
			frappe.throw(_("Purchase Invoice {0} not found.").format(self.purchase_invoice))
		if pi.docstatus != 1:
			frappe.throw(
				_("Purchase Invoice <b>{0}</b> must be submitted.").format(self.purchase_invoice)
			)
		if flt(pi.outstanding_amount) <= 0:
			frappe.throw(
				_("Purchase Invoice <b>{0}</b> has no outstanding amount.").format(self.purchase_invoice)
			)
		if pi.company != self.company:
			frappe.throw(
				_("Purchase Invoice <b>{0}</b> belongs to company <b>{1}</b>.").format(
					self.purchase_invoice, pi.company
				)
			)

		if not self.amount:
			self.amount = pi.outstanding_amount
		if flt(self.amount) > flt(pi.outstanding_amount) + 0.005:
			frappe.throw(
				_("Paid Amount cannot exceed the Purchase Invoice outstanding amount ({0}).").format(
					pi.outstanding_amount
				)
			)

	def _validate_accompanying(self):
		if not self.is_accompanying:
			self.set("purchase_orders", [])
			self.landed_cost_voucher = None
			self._validate_non_accompanying_category()
			return

		self._validate_accompanying_category()
		self._validate_purchase_orders()
		if self.payment_type == "Against Purchase Invoice" and self.purchase_invoice:
			mismatch = landed_cost.get_pi_category_account_mismatch(self)
			if mismatch:
				frappe.throw(mismatch)

	def _validate_non_accompanying_category(self):
		if not self.expense_category:
			return
		flagged = frappe.db.get_value(
			"Expense Category", self.expense_category, "is_accompanying_expense"
		)
		if flagged:
			frappe.throw(
				_(
					"The Expense Category <b>{0}</b> is marked as an Accompanying Expense Category. "
					"Either use a non-accompanying category or check <b>Is Accompanying Expense</b>."
				).format(self.expense_category)
			)
		self._validate_category_account(must_be_valuation=False)

	def _validate_accompanying_category(self):
		flagged = frappe.db.get_value(
			"Expense Category", self.expense_category, "is_accompanying_expense"
		)
		if not flagged:
			frappe.throw(
				_(
					"The Expense Category <b>{0}</b> is not marked as an Accompanying Expense Category."
				).format(self.expense_category)
			)
		self._validate_category_account(must_be_valuation=True)

	def _validate_category_account(self, must_be_valuation):
		expense_account = frappe.db.get_value(
			"Expense Category", self.expense_category, "expense_account"
		)
		if not expense_account:
			return
		account_type = frappe.db.get_value("Account", expense_account, "account_type")
		if must_be_valuation and account_type != VALUATION_ACCOUNT_TYPE:
			frappe.throw(
				_(
					"Expense Account <b>{0}</b> for category <b>{1}</b> must have Account Type "
					"<b>Expenses Included In Valuation</b>. Current type: <b>{2}</b>."
				).format(expense_account, self.expense_category, account_type or _("None"))
			)
		if not must_be_valuation and account_type == VALUATION_ACCOUNT_TYPE:
			frappe.throw(
				_(
					"Expense Account <b>{0}</b> for category <b>{1}</b> must not have Account Type "
					"<b>Expenses Included In Valuation</b>."
				).format(expense_account, self.expense_category)
			)

	def _validate_purchase_orders(self):
		po_names = self.purchase_order_names()
		if not po_names:
			frappe.throw(_("At least one Purchase Order is required for accompanying expenses."))
		if len(po_names) != len(set(po_names)):
			frappe.throw(_("Duplicate Purchase Order found. Each Purchase Order can only be added once."))

		for po_name in po_names:
			po = frappe.db.get_value(
				"Purchase Order", po_name, ["company", "docstatus"], as_dict=True
			)
			if not po:
				frappe.throw(_("Purchase Order <b>{0}</b> not found.").format(po_name))
			if po.docstatus != 1:
				frappe.throw(
					_("Purchase Order <b>{0}</b> must be submitted before linking it to an expense.").format(
						po_name
					)
				)
			if po.company != self.company:
				frappe.throw(
					_("Purchase Order <b>{0}</b> belongs to company <b>{1}</b>.").format(
						po_name, po.company
					)
				)

	def purchase_order_names(self):
		return landed_cost.expense_purchase_orders(self)

	def _validate_amount(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Paid Amount must be greater than zero."))

	def _validate_reference(self):
		if not self.paid_from:
			return
		account_type = frappe.get_cached_value("Account", self.paid_from, "account_type")
		if account_type == "Bank" and (not self.reference_no or not self.reference_date):
			frappe.throw(_("Reference No and Reference Date are mandatory for Bank payments."))
