import frappe
from frappe import _
from frappe.utils import has_common

ALLOWED_ROLES = ("Garage Service Advisor", "Garage Supervisor", "Garage Manager")


@frappe.whitelist(methods=["POST"])
def approve_additional_part(job_card, row_name, approve=True):
	if not has_common(ALLOWED_ROLES, frappe.get_roles()):
		frappe.throw(_("Not permitted to approve additional parts"), frappe.PermissionError)
	# Normalize approve param (could be string from JS)
	if isinstance(approve, str):
		approve = approve.lower() in ("1", "true", "yes")
	doc = frappe.get_doc("Garage Job Card", job_card)
	row = None
	for r in doc.additional_parts or []:
		if r.name == row_name:
			row = r
			break
	if not row:
		frappe.throw(_("Row {0} not found").format(row_name))
	new_status = "Approved" if approve else "Rejected"
	row.status = new_status
	# approved_by is Employee linked to current user
	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	if not employee:
		# fallback: first employee for this user? or just use session user as string if not found
		employee = frappe.db.get_value("Employee", {}, "name")
	row.approved_by = employee
	doc.flags.ignore_validate_update_after_submit = True
	doc.save(ignore_permissions=True)

	if approve and row.item_code:
		_update_quotation(doc, row)
	return {"status": new_status, "approved_by": row.approved_by}


def _update_quotation(job_card_doc, row):
	try:
		so_name = job_card_doc.service_order
		if not so_name:
			return
		so = frappe.get_doc("Service Order", so_name)
		if not so.quotation or not frappe.db.exists("Quotation", so.quotation):
			return
		quotation = frappe.get_doc("Quotation", so.quotation)
		# Check if item already exists
		for qi in quotation.items or []:
			if qi.item_code == row.item_code:
				return
		rate = frappe.db.get_value("Item", row.item_code, "valuation_rate") or 0
		quotation.append("items", {"item_code": row.item_code, "qty": row.qty or 1, "rate": rate})
		quotation.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="approve_additional_part quotation update failed", message=frappe.get_traceback())
