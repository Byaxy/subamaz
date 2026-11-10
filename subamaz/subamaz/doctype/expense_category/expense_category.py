# Copyright (c) 2026, SubaMaz Contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

VALUATION_ACCOUNT_TYPE = "Expenses Included In Valuation"


class ExpenseCategory(Document):
	def validate(self):
		if not self.is_accompanying_expense:
			return

		if not self.expense_account:
			frappe.throw(_("Expense Account is required for Accompanying Expense Categories."))

		account_type = frappe.db.get_value("Account", self.expense_account, "account_type")
		if account_type != VALUATION_ACCOUNT_TYPE:
			frappe.throw(
				_(
					"For Accompanying Expense Categories, the Expense Account must have "
					"Account Type <b>Expenses Included In Valuation</b>.<br><br>"
					"Current Account: <b>{0}</b><br>Current Type: <b>{1}</b>"
				).format(self.expense_account, account_type or _("None"))
			)
