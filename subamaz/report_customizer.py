# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

"""Inject Garage Vehicle columns into standard sales Query Reports.

Reuses the nbs_customization.report_customizer pattern: hooks.py routes
frappe.desk.query_report.run / export_query here, rows are enriched
post-execution so both the on-screen view and Excel/CSV export carry the
vehicle columns (registration number, make, type, model).

Only row-level reports (one row per order/invoice) are covered. Aggregated
trend reports (Sales Order Trends, Sales Invoice Trends, Sales Analytics)
group rows by period/party and carry no per-document reference, so vehicle
detail columns cannot apply to them.
"""

# Capture originals at import time — swapping _qr_module.run inside
# export_query would otherwise make these point back at us (recursion).
import frappe
import frappe.desk.query_report as _qr_module
from frappe import _
from frappe.desk.query_report import export_query as _ORIGINAL_EXPORT_QUERY
from frappe.desk.query_report import run as _ORIGINAL_RUN

CHUNK_SIZE = 500

# voucher_field: row key holding the Sales Order / Sales Invoice name.
# voucher_type_field: when set, only rows of that doctype are enriched
# (AR mixes invoices, payments and journal entries in one report).
REPORT_CONFIG = {
	"Sales Register": {
		"doctype": "Sales Invoice",
		"voucher_field": "voucher_no",
		"voucher_type_field": "voucher_type",
		"anchors": ["customer_name", "customer"],
	},
	"Sales Order Analysis": {
		"doctype": "Sales Order",
		"voucher_field": "sales_order",
		"anchors": ["customer", "sales_order"],
	},
	"Accounts Receivable": {
		"doctype": "Sales Invoice",
		"voucher_field": "voucher_no",
		"voucher_type_field": "voucher_type",
		"anchors": ["customer_name", "party"],
	},
}


def _vehicle_columns():
	return [
		{"label": _("Vehicle"), "fieldname": "vehicle_registration", "fieldtype": "Data", "width": 130},
		{"label": _("Vehicle Make"), "fieldname": "vehicle_make", "fieldtype": "Data", "width": 110},
		{"label": _("Vehicle Type"), "fieldname": "vehicle_type", "fieldtype": "Data", "width": 110},
		{"label": _("Vehicle Model"), "fieldname": "vehicle_model", "fieldtype": "Data", "width": 110},
	]


@frappe.whitelist()
def run(
	report_name: str,
	filters=None,
	user: str | None = None,
	ignore_prepared_report: bool = False,
	custom_columns=None,
	is_tree: bool = False,
	parent_field: str | None = None,
	are_default_filters: bool = True,
	js_filters=None,
):
	"""Wrapper around frappe.desk.query_report.run (see hooks.py)."""
	result = _ORIGINAL_RUN(
		report_name=report_name,
		filters=filters,
		user=user,
		ignore_prepared_report=ignore_prepared_report,
		custom_columns=custom_columns,
		is_tree=is_tree,
		parent_field=parent_field,
		are_default_filters=are_default_filters,
		js_filters=js_filters,
	)

	config = REPORT_CONFIG.get(report_name)
	if not config:
		return result

	try:
		return _apply_vehicle_columns(result, config)
	except Exception:
		frappe.log_error(
			title=f"SubaMaz report_customizer error for '{report_name}'",
			message=frappe.get_traceback(),
		)
		return result


@frappe.whitelist()
def export_query():
	"""Wrapper around frappe.desk.query_report.export_query.

	export_query calls run() via a direct module reference, bypassing the
	whitelisted-method dispatcher — so without this swap the export would
	contain the raw columns without vehicle data. try/finally restores the
	original before returning to the event loop.
	"""
	_saved_run = _qr_module.run
	_qr_module.run = run
	try:
		return _ORIGINAL_EXPORT_QUERY()
	finally:
		_qr_module.run = _saved_run


def _apply_vehicle_columns(result: dict, config: dict) -> dict:
	columns = result.get("columns") or []
	data = result.get("result") or []
	if not _rows_are_dicts(data):
		return result

	columns = [frappe.desk.query_report.get_column_as_dict(c) for c in columns]
	_enrich_rows_with_vehicle(data, config)
	columns = _insert_block_after(columns, _vehicle_columns(), config["anchors"])
	result["columns"] = columns
	result["result"] = data
	return result


def _rows_are_dicts(data: list) -> bool:
	return any(isinstance(row, dict) for row in data)


def _row_voucher(row: dict, config: dict) -> str | None:
	voucher_type_field = config.get("voucher_type_field")
	if voucher_type_field and row.get(voucher_type_field) not in (None, config["doctype"]):
		return None
	return row.get(config["voucher_field"])


def _enrich_rows_with_vehicle(data: list, config: dict) -> None:
	vouchers = sorted(
		{_row_voucher(row, config) for row in data if isinstance(row, dict) and _row_voucher(row, config)}
	)
	if not vouchers:
		return

	vehicle_by_voucher = {}
	for i in range(0, len(vouchers), CHUNK_SIZE):
		rows = frappe.get_all(
			config["doctype"],
			filters={"name": ["in", vouchers[i : i + CHUNK_SIZE]]},
			fields=["name", "garage_vehicle"],
		)
		for r in rows:
			if r.get("garage_vehicle"):
				vehicle_by_voucher[r["name"]] = r["garage_vehicle"]

	if not vehicle_by_voucher:
		return

	vehicles = {}
	for i in range(0, len(set(vehicle_by_voucher.values())), CHUNK_SIZE):
		names = sorted(set(vehicle_by_voucher.values()))[i : i + CHUNK_SIZE]
		for v in frappe.get_all(
			"Garage Vehicle",
			filters={"name": ["in", names]},
			fields=["name", "registration_number", "make", "type", "model"],
		):
			vehicles[v["name"]] = v

	for row in data:
		if not isinstance(row, dict):
			continue
		vehicle = vehicles.get(vehicle_by_voucher.get(_row_voucher(row, config) or "", "") or "")
		if not vehicle:
			continue
		row["vehicle_registration"] = vehicle.get("registration_number") or vehicle.get("name")
		row["vehicle_make"] = vehicle.get("make") or ""
		row["vehicle_type"] = vehicle.get("type") or ""
		row["vehicle_model"] = vehicle.get("model") or ""


def _insert_block_after(columns: list[dict], block: list[dict], anchors: list[str]) -> list[dict]:
	"""Insert block after the first anchor present; fallback to index 1."""
	present = {c.get("fieldname") for c in columns}
	if any(c.get("fieldname") == block[0].get("fieldname") for c in columns):
		return columns
	anchor = next((a for a in anchors if a in present), None)
	if anchor is None:
		return columns[:1] + block + columns[1:]
	out = []
	for col in columns:
		out.append(col)
		if col.get("fieldname") == anchor:
			out.extend(block)
	return out
