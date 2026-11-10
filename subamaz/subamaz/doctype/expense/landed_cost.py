# Copyright (c) 2026, SubaMaz Contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def expense_purchase_orders(expense):
	return [row.purchase_order for row in (expense.purchase_orders or []) if row.purchase_order]


def find_lcvs_for_expense(expense_name):
	if not frappe.get_meta("Landed Cost Voucher").has_field("custom_expense"):
		return []
	return frappe.get_all(
		"Landed Cost Voucher",
		filters={"custom_expense": expense_name, "docstatus": ["<", 2]},
		pluck="name",
	)


def check_purchase_order_fully_received(po_name):
	"""Return whether every item on a submitted Purchase Order is fully received."""
	po = frappe.db.get_value("Purchase Order", po_name, ["docstatus"], as_dict=True)
	if not po:
		frappe.throw(_("Purchase Order <b>{0}</b> not found.").format(po_name))
	if po.docstatus != 1:
		return {
			"ready": False,
			"message": _("Purchase Order <b>{0}</b> is not submitted.").format(po_name),
			"unreceived_items": [],
		}

	items = frappe.db.get_all(
		"Purchase Order Item",
		filters={"parent": po_name},
		fields=["item_code", "qty", "received_qty"],
	)
	if not items:
		return {
			"ready": False,
			"message": _("Purchase Order <b>{0}</b> has no items.").format(po_name),
			"unreceived_items": [],
		}

	unreceived = []
	for row in items:
		expected = flt(row.qty)
		received = flt(row.received_qty)
		if received + 0.005 < expected:
			unreceived.append(
				{
					"purchase_order": po_name,
					"item_code": row.item_code,
					"expected_qty": expected,
					"received_qty": received,
					"pending_qty": flt(expected - received, 3),
				}
			)

	if not unreceived:
		return {"ready": True, "message": None, "unreceived_items": []}

	lines = "".join(
		[
			"<li><b>{0}</b> — ordered {1}, received {2}, pending {3}</li>".format(
				row["item_code"], row["expected_qty"], row["received_qty"], row["pending_qty"]
			)
			for row in unreceived
		]
	)
	message = _(
		"Purchase Order <b>{0}</b> is not fully received:<br><ul>{1}</ul>"
		"All items must be received before creating a Landed Cost Voucher."
	).format(po_name, lines)
	return {"ready": False, "message": message, "unreceived_items": unreceived}


@frappe.whitelist()
def check_purchase_orders_fully_received(po_names):
	"""Check every Purchase Order. Accepts a list or a JSON string from the form."""
	po_names = _normalize_po_names(po_names)
	if not po_names:
		return {"ready": False, "message": _("Add at least one Purchase Order."), "unreceived_items": []}

	unreceived = []
	messages = []
	for po_name in po_names:
		result = check_purchase_order_fully_received(po_name)
		if not result["ready"]:
			unreceived.extend(result["unreceived_items"])
			if result["message"]:
				messages.append(result["message"])

	if unreceived:
		return {
			"ready": False,
			"message": "<br>".join(messages),
			"unreceived_items": unreceived,
		}
	return {"ready": True, "message": None, "unreceived_items": []}


def _normalize_po_names(po_names):
	if isinstance(po_names, str):
		try:
			po_names = frappe.parse_json(po_names)
		except ValueError:
			po_names = [po_names]
	if not po_names:
		return []
	if isinstance(po_names, str):
		po_names = [po_names]

	seen = set()
	ordered = []
	for name in po_names:
		if name and name not in seen:
			seen.add(name)
			ordered.append(name)
	return ordered


def get_purchase_receipts(po_names):
	"""All submitted, non-return Purchase Receipts referencing any of the POs."""
	if not po_names:
		return []
	return frappe.db.sql(
		"""
		SELECT DISTINCT
			pr.name AS receipt_document,
			pr.supplier,
			pr.grand_total
		FROM `tabPurchase Receipt` pr
		WHERE pr.docstatus = 1
			AND pr.is_return = 0
			AND EXISTS (
				SELECT 1 FROM `tabPurchase Receipt Item` pri
				WHERE pri.parent = pr.name
					AND pri.purchase_order IN %(pos)s
			)
		ORDER BY pr.posting_date ASC, pr.name ASC
		""",
		{"pos": tuple(po_names)},
		as_dict=True,
	)


def get_pi_category_account_mismatch(expense):
	"""Ensure an accompanying invoice flow books its cost to the category account."""
	if not (expense.payment_type == "Against Purchase Invoice" and expense.purchase_invoice):
		return None

	category_account = frappe.db.get_value(
		"Expense Category", expense.expense_category, "expense_account"
	)
	if not category_account:
		return None

	pi_accounts = list(
		{
			row["expense_account"]
			for row in frappe.db.get_all(
				"Purchase Invoice Item",
				filters={"parent": expense.purchase_invoice, "expense_account": ["is", "set"]},
				fields=["expense_account"],
			)
		}
	)
	if not pi_accounts:
		return None
	if len(pi_accounts) > 1:
		return _(
			"Purchase Invoice <b>{0}</b> books its cost to multiple expense accounts "
			"(<b>{1}</b>). The category <b>{2}</b> must match a single account so the "
			"Landed Cost Voucher clears it in full."
		).format(expense.purchase_invoice, ", ".join(sorted(pi_accounts)), expense.expense_category)
	if pi_accounts[0] != category_account:
		return _(
			"Purchase Invoice <b>{0}</b> books its cost to <b>{1}</b>, but Expense Category "
			"<b>{2}</b> points to <b>{3}</b>. Use a matching category or Direct Payment."
		).format(
			expense.purchase_invoice,
			pi_accounts[0],
			expense.expense_category,
			category_account,
		)
	return None


def validate_landed_cost_ready(expense):
	if not expense.is_accompanying:
		frappe.throw(_("This expense is not marked as an accompanying expense."))
	if expense.docstatus != 1:
		frappe.throw(_("The expense must be submitted before creating a Landed Cost Voucher."))
	if expense.landed_cost_voucher or find_lcvs_for_expense(expense.name):
		frappe.throw(
			_("A Landed Cost Voucher already exists for this expense: {0}").format(
				expense.landed_cost_voucher or ", ".join(find_lcvs_for_expense(expense.name))
			)
		)

	mismatch = get_pi_category_account_mismatch(expense)
	if mismatch:
		frappe.throw(mismatch)

	category_account = frappe.db.get_value(
		"Expense Category", expense.expense_category, "expense_account"
	)
	if not category_account:
		frappe.throw(
			_("No GL account configured for Expense Category <b>{0}</b>.").format(
				expense.expense_category
			)
		)

	po_names = expense_purchase_orders(expense)
	if not po_names:
		frappe.throw(_("Add at least one Purchase Order."))

	receipt_check = check_purchase_orders_fully_received(po_names)
	if not receipt_check["ready"]:
		frappe.throw(receipt_check["message"])

	receipts = get_purchase_receipts(po_names)
	if not receipts:
		frappe.throw(
			_("The linked Purchase Orders have no submitted Purchase Receipts yet.")
		)

	return po_names, receipts, category_account


@frappe.whitelist()
def make_landed_cost_voucher(source_name, target_doc=None):
	"""Return a new unsaved LCV, following the ERPNext create-document convention."""
	expense = frappe.get_doc("Expense", source_name)
	po_names, receipts, category_account = validate_landed_cost_ready(expense)

	if target_doc:
		lcv = frappe.get_doc(target_doc) if isinstance(target_doc, dict) else target_doc
	else:
		lcv = frappe.new_doc("Landed Cost Voucher")

	lcv.company = expense.company
	lcv.set("purchase_receipts", [])
	lcv.set("taxes", [])

	for row in receipts:
		lcv.append(
			"purchase_receipts",
			{
				"receipt_document_type": "Purchase Receipt",
				"receipt_document": row["receipt_document"],
				"supplier": row["supplier"],
				"grand_total": row["grand_total"],
			},
		)

	lcv.append(
		"taxes",
		{
			"description": expense.expense_description or expense.expense_category,
			"expense_account": category_account,
			"amount": expense.amount,
		},
	)

	if hasattr(lcv, "custom_expense"):
		lcv.custom_expense = expense.name
	if hasattr(lcv, "custom_linked_purchase_order"):
		lcv.custom_linked_purchase_order = po_names[0]
	if hasattr(lcv, "custom_linked_purchase_orders"):
		lcv.custom_linked_purchase_orders = ", ".join(po_names)

	return lcv


def validate_unique_expense_lcv(doc, method=None):
	"""Block a second live LCV for the same expense."""
	expense_name = doc.get("custom_expense")
	if not expense_name:
		return
	others = [name for name in find_lcvs_for_expense(expense_name) if name != doc.name]
	if others:
		frappe.throw(
			_("A Landed Cost Voucher already exists for Expense <b>{0}</b>: {1}").format(
				expense_name, ", ".join(others)
			)
		)


def link_expense_lcv(doc, method=None):
	expense_name = doc.get("custom_expense")
	if not expense_name or not frappe.db.exists("Expense", expense_name):
		return
	frappe.db.set_value(
		"Expense", expense_name, "landed_cost_voucher", doc.name, update_modified=False
	)


def unlink_expense_lcv(doc, method=None):
	expense_name = doc.get("custom_expense")
	if not expense_name or not frappe.db.exists("Expense", expense_name):
		return
	current = frappe.db.get_value("Expense", expense_name, "landed_cost_voucher")
	if current == doc.name:
		frappe.db.set_value("Expense", expense_name, "landed_cost_voucher", None, update_modified=False)


def cancel_linked_lcv(expense):
	names = []
	if expense.landed_cost_voucher:
		names.append(expense.landed_cost_voucher)
	for name in find_lcvs_for_expense(expense.name):
		if name not in names:
			names.append(name)

	for name in names:
		if not frappe.db.exists("Landed Cost Voucher", name):
			continue
		lcv = frappe.get_doc("Landed Cost Voucher", name)
		if lcv.docstatus == 1:
			lcv.cancel()
		elif lcv.docstatus == 0:
			frappe.delete_doc("Landed Cost Voucher", name, ignore_permissions=True)

	if expense.landed_cost_voucher:
		frappe.db.set_value("Expense", expense.name, "landed_cost_voucher", None, update_modified=False)
