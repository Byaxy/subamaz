import frappe
from frappe import _
from frappe.utils import has_common, now_datetime

ALLOWED_ROLES = ("Garage Technician", "Garage Supervisor", "Garage Manager")


def _gate():
	if not has_common(ALLOWED_ROLES, frappe.get_roles()):
		frappe.throw(_("You are not permitted to perform job card operations"), frappe.PermissionError)


def _get_job_card(name):
	doc = frappe.get_doc("Garage Job Card", name)
	return doc


def _get_technician_employee():
	# try to find Employee linked to current user
	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	return employee


@frappe.whitelist(methods=["POST"])
def start_job(job_card):
	_gate()
	doc = _get_job_card(job_card)
	if doc.status not in ("Draft", "Assigned", "Accepted", "Paused", "Waiting Parts", "Waiting Approval"):
		frappe.throw(_("Cannot start job from status {0}").format(doc.status))
	doc.status = "Working"
	# open a Time Log row if none open
	has_open = any(not r.finished_at for r in (doc.time_logs or []))
	if not has_open:
		technician = _get_technician_employee() or doc.lead_technician
		rate = frappe.db.get_value("Garage Department", doc.department, "default_hourly_rate") or 0
		doc.append(
			"time_logs",
			{
				"technician": technician,
				"started_at": now_datetime(),
				"hourly_rate": rate,
			},
		)
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def pause_job(job_card):
	_gate()
	doc = _get_job_card(job_card)
	if doc.status != "Working":
		frappe.throw(_("Can only pause a Working job (current: {0})").format(doc.status))
	# close open Time Log
	for row in doc.time_logs or []:
		if not row.finished_at:
			row.finished_at = now_datetime()
			if row.started_at and row.finished_at:
				try:
					from frappe.utils import time_diff_in_hours

					row.hours = time_diff_in_hours(row.finished_at, row.started_at)
					row.labour_cost = (row.hours or 0) * (row.hourly_rate or 0)
				except Exception:
					pass
			break
	doc.status = "Paused"
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def complete_job(job_card):
	_gate()
	doc = _get_job_card(job_card)
	if doc.status not in ("Working", "Paused", "Ready QA"):
		# allow from Working/Paused via API
		if doc.status == "Draft":
			frappe.throw(_("Cannot complete a Draft job — start it first"))
	# close any open Time Logs
	for row in doc.time_logs or []:
		if not row.finished_at:
			row.finished_at = now_datetime()
			if row.started_at:
				try:
					from frappe.utils import time_diff_in_hours

					row.hours = time_diff_in_hours(row.finished_at, row.started_at)
					row.labour_cost = (row.hours or 0) * (row.hourly_rate or 0)
				except Exception:
					pass
	doc.status = "Ready QA"
	doc.save()
	# optionally submit if needed
	if doc.docstatus == 0:
		doc.submit()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def consume_part(job_card, item_code, qty, warehouse=None):
	if not has_common(("Garage Technician", "Garage Supervisor", "Garage Manager"), frappe.get_roles()):
		frappe.throw(_("Not permitted to consume parts"), frappe.PermissionError)
	doc = _get_job_card(job_card)
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item {0} not found").format(item_code))
	qty = float(qty or 0)
	if qty <= 0:
		frappe.throw(_("Qty must be positive"))
	if not warehouse:
		warehouse = frappe.db.get_value("Warehouse", {}, "name")
		if not warehouse:
			frappe.throw(_("No warehouse found for consumption"))
	if not frappe.db.exists("Warehouse", warehouse):
		frappe.throw(_("Warehouse {0} not found").format(warehouse))

	rate = frappe.db.get_value("Item", item_code, "valuation_rate") or 0
	amount = qty * float(rate or 0)
	warehouse_company = frappe.db.get_value("Warehouse", warehouse, "company")

	stock_entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Issue",
			"purpose": "Material Issue",
			"company": warehouse_company,
			"from_warehouse": warehouse,
			"garage_job_card": doc.name,
			"items": [
				{
					"item_code": item_code,
					"qty": qty,
					"s_warehouse": warehouse,
					"basic_rate": rate,
				}
			],
		}
	)
	stock_entry.insert(ignore_permissions=True)
	stock_entry.flags.ignore_permissions = True
	try:
		stock_entry.submit()
	except Exception:
		frappe.log_error(title="consume_part Stock Entry submit failed", message=frappe.get_traceback())
		raise

	doc.append(
		"consumed_parts",
		{
			"item_code": item_code,
			"qty": qty,
			"warehouse": warehouse,
			"rate": rate,
			"amount": amount,
			"stock_entry": stock_entry.name,
		},
	)
	doc.save()
	return {"stock_entry": stock_entry.name, "job_card": doc.name}
