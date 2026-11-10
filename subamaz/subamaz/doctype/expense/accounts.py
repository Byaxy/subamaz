# Copyright (c) 2026, SubaMaz Contributors
# For license information, please see license.txt

import frappe
from frappe import _


def set_company_defaults(doc):
	if not doc.company:
		doc.company = frappe.defaults.get_user_default("Company")
	if not doc.cost_center and doc.company:
		doc.cost_center = frappe.db.get_value("Company", doc.company, "cost_center")


def resolve_payment_account(doc):
	"""Default paid_from from the Mode of Payment. The field is read-only in the form."""
	if not doc.mode_of_payment or doc.paid_from:
		return
	account = get_mop_default_account(doc.mode_of_payment, doc.company)
	if account:
		doc.paid_from = account


def get_mop_default_account(mode_of_payment, company):
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

	account = get_bank_cash_account(mode_of_payment, company)
	return account.get("account") if account else None


def resolve_paid_to(doc):
	if doc.payment_type == "Against Purchase Invoice" and doc.purchase_invoice:
		from erpnext.accounts.party import get_party_account

		supplier = frappe.db.get_value("Purchase Invoice", doc.purchase_invoice, "supplier")
		if supplier:
			doc.paid_to = get_party_account("Supplier", supplier, doc.company)
		return

	if doc.expense_category:
		doc.paid_to = frappe.db.get_value("Expense Category", doc.expense_category, "expense_account")


def set_account_currencies(doc):
	doc.paid_from_account_currency = (
		frappe.db.get_value("Account", doc.paid_from, "account_currency") if doc.paid_from else None
	)
	doc.paid_to_account_currency = (
		frappe.db.get_value("Account", doc.paid_to, "account_currency") if doc.paid_to else None
	)


def validate_paid_from(doc):
	if not doc.mode_of_payment or not doc.paid_from:
		return

	expected = get_mop_default_account(doc.mode_of_payment, doc.company)
	if not expected:
		frappe.throw(
			_("Mode of Payment <b>{0}</b> has no paying account configured for company <b>{1}</b>.").format(
				doc.mode_of_payment, doc.company
			)
		)
	if doc.paid_from != expected:
		frappe.throw(
			_(
				"Account Paid From <b>{0}</b> does not match Payment Method <b>{1}</b> "
				"(expected <b>{2}</b>). It is set automatically."
			).format(doc.paid_from, doc.mode_of_payment, expected)
		)

	details = frappe.db.get_value(
		"Account",
		doc.paid_from,
		["company", "is_group", "disabled"],
		as_dict=True,
	)
	if not details:
		frappe.throw(_("Account Paid From <b>{0}</b> not found.").format(doc.paid_from))
	if details.company != doc.company:
		frappe.throw(
			_("Account Paid From <b>{0}</b> belongs to another company.").format(doc.paid_from)
		)
	if details.is_group:
		frappe.throw(
			_("Account Paid From <b>{0}</b> is a group account and cannot be used.").format(doc.paid_from)
		)
	if details.disabled:
		frappe.throw(_("Account Paid From <b>{0}</b> is disabled.").format(doc.paid_from))


def validate_paid_to(doc):
	if not doc.paid_to:
		return
	details = frappe.db.get_value(
		"Account",
		doc.paid_to,
		["company", "is_group", "disabled"],
		as_dict=True,
	)
	if not details:
		frappe.throw(_("Account Paid To <b>{0}</b> not found.").format(doc.paid_to))
	if details.company != doc.company:
		frappe.throw(_("Account Paid To <b>{0}</b> belongs to another company.").format(doc.paid_to))
	if details.is_group:
		frappe.throw(
			_("Account Paid To <b>{0}</b> is a group account and cannot be used.").format(doc.paid_to)
		)
	if details.disabled:
		frappe.throw(_("Account Paid To <b>{0}</b> is disabled.").format(doc.paid_to))


def validate_single_currency(doc):
	"""Posting is limited to company-currency accounts; no implicit FX conversion."""
	company_currency = frappe.get_cached_value("Company", doc.company, "default_currency")
	if doc.paid_from_account_currency and doc.paid_from_account_currency != company_currency:
		frappe.throw(
			_("Expense posting only supports accounts in company currency ({0}).").format(company_currency)
		)
	if doc.paid_to_account_currency and doc.paid_to_account_currency != company_currency:
		frappe.throw(
			_("Expense posting only supports accounts in company currency ({0}).").format(company_currency)
		)
	if doc.payment_type == "Against Purchase Invoice" and doc.purchase_invoice:
		pi_currency = frappe.db.get_value("Purchase Invoice", doc.purchase_invoice, "currency")
		if pi_currency != company_currency:
			frappe.throw(
				_(
					"Purchase Invoice <b>{0}</b> is in <b>{1}</b>. Expense payment only supports "
					"company currency ({2})."
				).format(doc.purchase_invoice, pi_currency, company_currency)
			)


def create_journal_entry(doc):
	category_account = frappe.db.get_value(
		"Expense Category", doc.expense_category, "expense_account"
	)
	if not category_account:
		frappe.throw(
			_("No GL account configured for Expense Category <b>{0}</b>.").format(doc.expense_category)
		)

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = doc.company
	je.posting_date = doc.expense_date
	je.mode_of_payment = doc.mode_of_payment
	je.cheque_no = doc.reference_no
	je.cheque_date = doc.reference_date
	je.user_remark = _("Expense: {0} — {1} | Payee: {2}").format(
		doc.name, doc.expense_description, doc.payee or _("N/A")
	)
	cost_center = doc.cost_center or frappe.db.get_value("Company", doc.company, "cost_center")

	je.append(
		"accounts",
		{
			"account": category_account,
			"debit_in_account_currency": doc.amount,
			"credit_in_account_currency": 0,
			"cost_center": cost_center,
		},
	)
	je.append(
		"accounts",
		{
			"account": doc.paid_from,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": doc.amount,
			"cost_center": cost_center,
		},
	)

	je.insert(ignore_permissions=True)
	je.submit()
	doc.db_set("journal_entry", je.name)


def reverse_journal_entry(doc):
	if not doc.get("journal_entry"):
		return
	je = frappe.get_doc("Journal Entry", doc.journal_entry)
	if je.docstatus == 1:
		je.cancel()
	doc.db_set("journal_entry", None)


def create_payment_entry(doc):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	pi_currency = frappe.db.get_value("Purchase Invoice", doc.purchase_invoice, "currency")
	if pi_currency != doc.paid_from_account_currency:
		frappe.throw(
			_(
				"Currency mismatch: Purchase Invoice is in <b>{0}</b>, but Account Paid From is in "
				"<b>{1}</b>. Use a matching bank/cash account."
			).format(pi_currency, doc.paid_from_account_currency)
		)

	pe = get_payment_entry("Purchase Invoice", doc.purchase_invoice)
	pe.posting_date = doc.expense_date
	pe.paid_from = doc.paid_from
	pe.paid_amount = doc.amount
	pe.received_amount = doc.amount
	pe.source_exchange_rate = 1
	pe.target_exchange_rate = 1
	pe.mode_of_payment = doc.mode_of_payment
	pe.reference_no = doc.reference_no
	pe.reference_date = doc.reference_date or doc.expense_date
	pe.remarks = _("Payment via Expense {0} — {1} | Payee: {2}").format(
		doc.name, doc.expense_description, doc.payee
	)

	for ref in pe.references:
		if ref.reference_name == doc.purchase_invoice:
			ref.allocated_amount = min(doc.amount, ref.outstanding_amount)

	pe.insert(ignore_permissions=True)
	pe.submit()
	doc.db_set("payment_entry", pe.name)


def reverse_payment_entry(doc):
	if not doc.get("payment_entry"):
		return
	pe = frappe.get_doc("Payment Entry", doc.payment_entry)
	if pe.docstatus == 1:
		pe.cancel()
	doc.db_set("payment_entry", None)
