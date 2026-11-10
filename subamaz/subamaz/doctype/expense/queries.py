# Copyright (c) 2026, SubaMaz Contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_invoice_details(purchase_invoice: str):
	"""Return the fields needed to prefill the Expense form from a Purchase Invoice."""
	pi = frappe.db.get_value(
		"Purchase Invoice",
		purchase_invoice,
		[
			"outstanding_amount",
			"supplier",
			"supplier_name",
			"company",
			"bill_no",
			"docstatus",
			"currency",
		],
		as_dict=True,
	)
	if not pi:
		frappe.throw(_("Purchase Invoice {0} not found.").format(purchase_invoice))
	if pi.docstatus != 1:
		frappe.throw(_("Purchase Invoice {0} is not submitted.").format(purchase_invoice))
	if pi.outstanding_amount <= 0:
		frappe.throw(_("Purchase Invoice {0} has no outstanding amount.").format(purchase_invoice))
	return pi


@frappe.whitelist()
def get_payment_method_account(mode_of_payment: str, company: str):
	"""Resolve the Cash/Bank account configured on a Mode of Payment."""
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

	account = get_bank_cash_account(mode_of_payment, company)
	account_name = account.get("account") if account else None
	return {
		"account": account_name,
		"account_currency": (
			frappe.db.get_value("Account", account_name, "account_currency") if account_name else None
		),
	}


@frappe.whitelist()
def get_supplier_payable_details(supplier: str, company: str):
	"""Return the supplier payable account and its currency for a company."""
	from erpnext.accounts.party import get_party_account

	payable_account = get_party_account("Supplier", supplier, company)
	return {
		"paid_to": payable_account,
		"account_currency": frappe.db.get_value("Account", payable_account, "account_currency"),
	}


def get_purchase_invoices_search(doctype, txt, searchfield, start, page_len, filters):
	"""Link search for unpaid submitted Purchase Invoices."""
	company = (filters or {}).get("company") if isinstance(filters, dict) else None
	return frappe.db.sql(
		"""
		SELECT
			pi.name,
			pi.supplier_name,
			pi.grand_total,
			pi.outstanding_amount,
			pi.posting_date
		FROM `tabPurchase Invoice` pi
		WHERE pi.docstatus = 1
			AND pi.status NOT IN ('Paid', 'Cancelled')
			AND (%(company)s IS NULL OR pi.company = %(company)s)
			AND (
				pi.name LIKE %(txt)s
				OR IFNULL(pi.supplier_name, '') LIKE %(txt)s
				OR IFNULL(pi.bill_no, '') LIKE %(txt)s
			)
		ORDER BY pi.posting_date DESC, pi.name DESC
		LIMIT %(page_len)s OFFSET %(start)s
		""",
		{
			"company": company,
			"txt": f"%{txt}%",
			"page_len": page_len,
			"start": start,
		},
	)


def get_purchase_orders_search(doctype, txt, searchfield, start, page_len, filters):
	"""Link search for submitted Purchase Orders."""
	company = (filters or {}).get("company") if isinstance(filters, dict) else None
	return frappe.db.sql(
		"""
		SELECT
			po.name,
			po.supplier_name,
			po.grand_total,
			po.transaction_date
		FROM `tabPurchase Order` po
		WHERE po.docstatus = 1
			AND po.status != 'Cancelled'
			AND (%(company)s IS NULL OR po.company = %(company)s)
			AND (
				po.name LIKE %(txt)s
				OR IFNULL(po.supplier_name, '') LIKE %(txt)s
			)
		ORDER BY po.transaction_date DESC, po.name DESC
		LIMIT %(page_len)s OFFSET %(start)s
		""",
		{
			"company": company,
			"txt": f"%{txt}%",
			"page_len": page_len,
			"start": start,
		},
	)
