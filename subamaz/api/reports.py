# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate

from subamaz.api.access_control import has_capability


def _require_insights():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not has_capability(frappe.session.user, "module:insights"):
		frappe.throw(_("Not permitted — missing insights capability"), frappe.PermissionError)


def _parse_date(value):
	if not value:
		return None
	try:
		return getdate(value)
	except Exception:
		return None


def _previous_period(from_date, to_date):
	"""Return (prev_from, prev_to) for vs-previous % calc."""
	if not from_date or not to_date:
		return None, None
	delta = (to_date - from_date).days + 1
	prev_to = add_days(from_date, -1)
	prev_from = add_days(prev_to, -delta + 1)
	return getdate(prev_from), getdate(prev_to)


def _in_range(doctype, date_field, from_date, to_date, extra_filters=None):
	filters = {}
	if from_date:
		filters[date_field] = [">=", from_date]
		if to_date:
			filters[date_field] = ["between", [from_date, to_date]]
	elif to_date:
		filters[date_field] = ["<=", to_date]
	if extra_filters:
		filters.update(extra_filters)
	# use get_all with filters that support between
	# frappe's filter for between needs tuple
	return filters


# ---------------------------------------------------------------------------
# Overview widgets (reused by SPA + fallback Workspace)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_overview_stats(from_date=None, to_date=None):
	"""Aggregate Overview stat cards."""
	_require_insights()
	from_date = _parse_date(from_date) or getdate(add_days(nowdate(), -30))
	to_date = _parse_date(to_date) or getdate(nowdate())
	prev_from, prev_to = _previous_period(from_date, to_date)

	# Jobs Completed — Garage Job Card submitted & Completed
	jobs_q = """
		SELECT COUNT(*) as cnt
		FROM `tabGarage Job Card`
		WHERE docstatus=1
		  AND status IN ('Completed','Ready QA')
		  AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
	"""
	jobs_count = frappe.db.sql(jobs_q, {"from_date": from_date, "to_date": to_date}, as_dict=True)[0]["cnt"] or 0
	jobs_prev = frappe.db.sql(jobs_q, {"from_date": prev_from, "to_date": prev_to}, as_dict=True)[0]["cnt"] or 0 if prev_from else 0
	jobs_change = ((jobs_count - jobs_prev) / jobs_prev * 100) if jobs_prev else (100.0 if jobs_count else 0)

	# Revenue — Sales Invoice grand_total submitted in period
	rev_q = """
		SELECT COALESCE(SUM(grand_total),0) as total
		FROM `tabSales Invoice`
		WHERE docstatus=1
		  AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	"""
	revenue_total = frappe.db.sql(rev_q, {"from_date": from_date, "to_date": to_date}, as_dict=True)[0]["total"] or 0
	revenue_prev = frappe.db.sql(rev_q, {"from_date": prev_from, "to_date": prev_to}, as_dict=True)[0]["total"] or 0 if prev_from else 0
	revenue_change = ((revenue_total - revenue_prev) / revenue_prev * 100) if revenue_prev else (100.0 if revenue_total else 0)

	# Gross margin % — (revenue - cost)/revenue ; cost = sum of Job Card actual_cost in period (best effort)
	try:
		cost_q = """
			SELECT COALESCE(SUM(actual_cost),0) as cost
			FROM `tabGarage Job Card`
			WHERE docstatus<2 AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
		"""
		cost_total = frappe.db.sql(cost_q, {"from_date": from_date, "to_date": to_date}, as_dict=True)[0]["cost"] or 0
		gross_margin = ((revenue_total - cost_total) / revenue_total * 100) if revenue_total else 0
	except Exception:
		gross_margin = 0

	# Active Job Cards — not Completed/Cancelled
	active = frappe.db.count(
		"Garage Job Card",
		filters={"docstatus": ["<", 2], "status": ["not in", ["Completed", "Cancelled"]]},
	)

	# Outstanding Invoices — Sales Invoice outstanding_amount >0
	try:
		out_q = """
			SELECT COUNT(*) as cnt, COALESCE(SUM(outstanding_amount),0) as total
			FROM `tabSales Invoice`
			WHERE docstatus=1 AND outstanding_amount > 0
		"""
		out_row = frappe.db.sql(out_q, as_dict=True)[0]
		outstanding_count = out_row["cnt"] or 0
		outstanding_total = out_row["total"] or 0
	except Exception:
		outstanding_count = 0
		outstanding_total = 0

	return {
		"jobs_completed": int(jobs_count),
		"jobs_completed_prev": int(jobs_prev),
		"jobs_completed_change_pct": round(jobs_change, 2),
		"revenue_total": float(revenue_total),
		"revenue_prev_total": float(revenue_prev),
		"revenue_change_pct": round(revenue_change, 2),
		"gross_margin_pct": round(gross_margin, 2),
		"active_job_cards": int(active),
		"outstanding_invoices_total": float(outstanding_total),
		"outstanding_invoices_count": int(outstanding_count),
		"from_date": str(from_date),
		"to_date": str(to_date),
	}


@frappe.whitelist()
def get_revenue_trend(from_date=None, to_date=None):
	"""Monthly revenue series for chart."""
	_require_insights()
	from_date = _parse_date(from_date) or getdate(add_days(nowdate(), -90))
	to_date = _parse_date(to_date) or getdate(nowdate())
	rows = frappe.db.sql(
		"""
		SELECT DATE_FORMAT(posting_date, '%%Y-%%m') as period,
		       COALESCE(SUM(grand_total),0) as revenue
		FROM `tabSales Invoice`
		WHERE docstatus=1
		  AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY period
		ORDER BY period
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	return {"from_date": str(from_date), "to_date": str(to_date), "series": rows}


@frappe.whitelist()
def get_money_in_breakdown(from_date=None, to_date=None):
	"""Payment Entry grouped by mode_of_payment."""
	_require_insights()
	from_date = _parse_date(from_date) or getdate(add_days(nowdate(), -30))
	to_date = _parse_date(to_date) or getdate(nowdate())
	rows = frappe.db.sql(
		"""
		SELECT mode_of_payment as mode, COALESCE(SUM(paid_amount),0) as total
		FROM `tabPayment Entry`
		WHERE docstatus=1
		  AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY mode_of_payment
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	# normalize mode names
	for r in rows:
		if not r["mode"]:
			r["mode"] = "Unknown"
	return {"from_date": str(from_date), "to_date": str(to_date), "breakdown": rows}


@frappe.whitelist()
def get_receivables_aging():
	"""Aging buckets + Top Outstanding Customers."""
	_require_insights()
	rows = frappe.db.sql(
		"""
		SELECT name, customer, due_date, outstanding_amount, posting_date
		FROM `tabSales Invoice`
		WHERE docstatus=1 AND outstanding_amount > 0
		""",
		as_dict=True,
	)
	buckets = {"current_0_30": 0, "over_30_60": 0, "overdue_60_plus": 0}
	customer_totals = {}
	for r in rows:
		due = getdate(r["due_date"]) if r.get("due_date") else getdate(r["posting_date"])
		age = (getdate(nowdate()) - due).days if due else 0
		amt = float(r["outstanding_amount"] or 0)
		if age <= 30:
			buckets["current_0_30"] += amt
		elif age <= 60:
			buckets["over_30_60"] += amt
		else:
			buckets["overdue_60_plus"] += amt
		customer_totals[r["customer"]] = customer_totals.get(r["customer"], 0) + amt

	top_customers = sorted(
		[{"customer": k, "outstanding": v} for k, v in customer_totals.items()],
		key=lambda x: x["outstanding"],
		reverse=True,
	)[:10]
	return {"buckets": buckets, "top_customers": top_customers}


# ---------------------------------------------------------------------------
# run_report — thin wrapper over Report / in-code registry
# ---------------------------------------------------------------------------

# In-code registry for the 12 garage reports. Column definitions are minimal but
# valid for desk and for api callers. Each handler returns (columns, data).
REPORT_REGISTRY = {}


def _register(name, ref_doctype, handler, columns):
	REPORT_REGISTRY[name] = {"ref_doctype": ref_doctype, "columns": columns, "handler": handler}


def ensure_garage_reports():
	"""Idempotently create 12 Report docs (is_standard=1, module Subamaz)."""
	if not frappe.db.exists("DocType", "Report"):
		return
	for name, info in REPORT_REGISTRY.items():
		if frappe.db.exists("Report", name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Report",
				"report_name": name,
				"ref_doctype": info["ref_doctype"],
				"module": "Subamaz",
				"is_standard": "Yes",
				"report_type": "Script Report",
				"prepared_report": 0,
				"disabled": 0,
			}
		)
		try:
			doc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title="ensure_garage_reports failed", message=frappe.get_traceback())


def ensure_garage_workspace():
	"""Minimal Desk fallback Workspace + Number Cards + Dashboard Chart."""
	if not frappe.db.exists("DocType", "Workspace"):
		return
	# Number Cards
	cards = [
		{
			"label": "Active Job Cards",
			"name": "Active Job Cards",
			"document_type": "Garage Job Card",
			"function": "Count",
			"filters_json": '[["Garage Job Card","status","not in","Completed, Cancelled"],["Garage Job Card","docstatus","<","2"]]',
			"is_standard": 1,
			"is_public": 1,
		},
		{
			"label": "Outstanding Invoices",
			"name": "Outstanding Invoices",
			"document_type": "Sales Invoice",
			"function": "Count",
			"filters_json": '[["Sales Invoice","outstanding_amount",">","0"],["Sales Invoice","docstatus","=","1"]]',
			"is_standard": 1,
			"is_public": 1,
		},
		{
			"label": "Jobs Completed This Month",
			"name": "Jobs Completed This Month",
			"document_type": "Garage Job Card",
			"function": "Count",
			"filters_json": '[["Garage Job Card","status","=","Completed"],["Garage Job Card","docstatus","=","1"]]',
			"is_standard": 1,
			"is_public": 1,
		},
		{
			"label": "Revenue This Month",
			"name": "Revenue This Month",
			"document_type": "Sales Invoice",
			"function": "Sum",
			"aggregate_function_based_on": "grand_total",
			"filters_json": '[["Sales Invoice","docstatus","=","1"]]',
			"is_standard": 1,
			"is_public": 1,
		},
	]
	for c in cards:
		if not frappe.db.exists("Number Card", c["name"]):
			try:
				doc = frappe.get_doc({"doctype": "Number Card", "module": "Subamaz", "type": "Document Type", **c})
				doc.insert(ignore_permissions=True)
			except Exception:
				pass
	# Dashboard Chart
	if not frappe.db.exists("Dashboard Chart", "Revenue Trend"):
		try:
			doc = frappe.get_doc(
				{
					"doctype": "Dashboard Chart",
					"chart_name": "Revenue Trend",
					"module": "Subamaz",
					"is_standard": 1,
					"is_public": 1,
					"chart_type": "Sum",
					"document_type": "Sales Invoice",
					"source": "",
					"based_on": "posting_date",
					"value_based_on": "grand_total",
					"group_by_type": "Count",
					"time_interval": "Monthly",
					"timespan": "Last Year",
					"type": "Line",
					"timeseries": 1,
					"filters_json": '[["Sales Invoice","docstatus","=","1"]]',
				}
			)
			doc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title="ensure_garage_workspace chart failed", message=frappe.get_traceback())
	# Workspace
	if not frappe.db.exists("Workspace", "Garage Overview"):
		try:
			content = '[{"id":"head","type":"header","data":{"text":"Garage Overview","col":12}}]'
			doc = frappe.get_doc(
				{
					"doctype": "Workspace",
					"label": "Garage Overview",
					"title": "Garage Overview",
					"module": "Subamaz",
					"is_standard": 1,
					"public": 1,
					"content": content,
					"number_cards": [
						{"label": c["label"], "number_card_name": c["name"]}
						for c in cards
						if frappe.db.exists("Number Card", c["name"])
					],
					"charts": [{"label": "Revenue Trend", "chart_name": "Revenue Trend"}]
					if frappe.db.exists("Dashboard Chart", "Revenue Trend")
					else [],
					"links": [
						{"label": "Garage Vehicle", "type": "Link", "link_type": "DocType", "link_to": "Garage Vehicle", "onboard": 0},
						{"label": "Vehicle Reception", "type": "Link", "link_type": "DocType", "link_to": "Vehicle Reception", "onboard": 0},
						{"label": "Service Order", "type": "Link", "link_type": "DocType", "link_to": "Service Order", "onboard": 0},
						{"label": "Garage Job Card", "type": "Link", "link_type": "DocType", "link_to": "Garage Job Card", "onboard": 0},
						{"label": "Reports", "type": "Link", "link_type": "Report", "link_to": "Revenue by Month", "onboard": 0},
					],
					"shortcuts": [],
					"sequence_id": 7,
					"for_user": "",
				}
			)
			doc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title="ensure_garage_workspace failed", message=frappe.get_traceback())


def _col(label, fieldname, fieldtype="Data", width=120, options=None):
	c = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype, "width": width}
	if options:
		c["options"] = options
	return c


# Handlers — each queries garage/ERPNext tables directly. Keep SQL portable (MariaDB).


def _report_job_turnaround(filters):
	rows = frappe.db.sql(
		"""
		SELECT name as job_card, service_order, department, lead_technician,
		       status, DATEDIFF(modified, creation) as days_open
		FROM `tabGarage Job Card`
		WHERE docstatus<2
		ORDER BY creation DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	cols = [
		_col("Job Card", "job_card", "Link", 140, "Garage Job Card"),
		_col("Service Order", "service_order", "Link", 140, "Service Order"),
		_col("Department", "department", "Link", 120, "Garage Department"),
		_col("Technician", "lead_technician", "Link", 120, "Employee"),
		_col("Status", "status", "Data", 100),
		_col("Days Open", "days_open", "Int", 90),
	]
	return cols, rows


def _report_jobs_completed(filters):
	from_date = filters.get("from_date") or add_days(nowdate(), -30)
	to_date = filters.get("to_date") or nowdate()
	rows = frappe.db.sql(
		"""
		SELECT DATE(creation) as date, COUNT(*) as count, department
		FROM `tabGarage Job Card`
		WHERE docstatus=1 AND status IN ('Completed','Ready QA')
		  AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY DATE(creation), department
		ORDER BY date
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	cols = [_col("Date", "date", "Date", 120), _col("Count", "count", "Int", 90), _col("Department", "department", "Link", 120, "Garage Department")]
	return cols, rows


def _report_technician_productivity(filters):
	rows = frappe.db.sql(
		"""
		SELECT t.technician, SUM(t.hours) as total_hours, SUM(t.labour_cost) as total_cost, COUNT(*) as logs
		FROM `tabTime Log Entry` t
		JOIN `tabGarage Job Card` j ON j.name = t.parent AND j.docstatus<2
		GROUP BY t.technician
		ORDER BY total_hours DESC
		""",
		as_dict=True,
	)
	cols = [
		_col("Technician", "technician", "Link", 140, "Employee"),
		_col("Hours", "total_hours", "Float", 90),
		_col("Labour Cost", "total_cost", "Currency", 120),
		_col("Logs", "logs", "Int", 80),
	]
	return cols, rows


def _report_repairs_by_type(filters):
	rows = frappe.db.sql(
		"""
		SELECT inspection_type as type, COUNT(*) as count, AVG(mileage) as avg_mileage
		FROM `tabVehicle Inspection`
		WHERE docstatus<2
		GROUP BY inspection_type
		ORDER BY count DESC
		""",
		as_dict=True,
	)
	cols = [_col("Inspection Type", "type", "Data", 150), _col("Count", "count", "Int", 80), _col("Avg Mileage", "avg_mileage", "Float", 110)]
	return cols, rows


def _report_parts_usage(filters):
	from_date = filters.get("from_date") or add_days(nowdate(), -30)
	to_date = filters.get("to_date") or nowdate()
	rows = frappe.db.sql(
		"""
		SELECT item_code as item, SUM(qty) as qty, SUM(amount) as amount, COUNT(*) as entries
		FROM `tabConsumed Part Entry`
		JOIN `tabGarage Job Card` j ON j.name = parent AND j.docstatus<2
		WHERE j.creation BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY item_code
		ORDER BY amount DESC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	if not rows:
		# fallback to Stock Entry consumption linked to job card
		rows = frappe.db.sql(
			"""
			SELECT item_code as item, SUM(qty) as qty, SUM(basic_rate*qty) as amount
			FROM `tabStock Entry Detail`
			WHERE parent IN (SELECT name FROM `tabStock Entry` WHERE garage_job_card IS NOT NULL AND docstatus=1)
			GROUP BY item_code
			ORDER BY amount DESC
			""",
			as_dict=True,
		)
	cols = [_col("Item", "item", "Link", 140, "Item"), _col("Qty", "qty", "Float", 90), _col("Amount", "amount", "Currency", 120), _col("Entries", "entries", "Int", 80)]
	return cols, rows


def _report_slow_moving(filters):
	days = int(filters.get("days") or 90)
	cutoff = add_days(nowdate(), -days)
	rows = frappe.db.sql(
		"""
		SELECT i.item_code as item, i.item_name, COALESCE(SUM(c.qty),0) as consumed
		FROM `tabItem` i
		LEFT JOIN `tabConsumed Part Entry` c ON c.item_code=i.item_code
		LEFT JOIN `tabGarage Job Card` j ON j.name=c.parent AND j.docstatus<2 AND j.creation>=%(cutoff)s
		WHERE i.is_stock_item=1
		GROUP BY i.item_code, i.item_name
		HAVING consumed=0 OR consumed < 2
		ORDER BY consumed ASC
		LIMIT 200
		""",
		{"cutoff": cutoff},
		as_dict=True,
	)
	cols = [_col("Item", "item", "Link", 140, "Item"), _col("Item Name", "item_name", "Data", 200), _col("Consumed", "consumed", "Float", 90)]
	return cols, rows


def _report_stock_variance(filters):
	rows = frappe.db.sql(
		"""
		SELECT item_code as item, warehouse, actual_qty as system_qty
		FROM `tabBin`
		ORDER BY item_code LIMIT 200
		""",
		as_dict=True,
	)
	cols = [_col("Item", "item", "Link", 140, "Item"), _col("Warehouse", "warehouse", "Link", 120, "Warehouse"), _col("System Qty", "system_qty", "Float", 100)]
	return cols, rows


def _report_stock_transfers(filters):
	from_date = filters.get("from_date") or add_days(nowdate(), -30)
	to_date = filters.get("to_date") or nowdate()
	rows = frappe.db.sql(
		"""
		SELECT name, posting_date, from_warehouse, to_warehouse, stock_entry_type
		FROM `tabStock Entry`
		WHERE docstatus=1 AND purpose='Material Transfer'
		  AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY posting_date DESC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	cols = [_col("Stock Entry", "name", "Link", 140, "Stock Entry"), _col("Posting Date", "posting_date", "Date", 110), _col("From", "from_warehouse", "Link", 120, "Warehouse"), _col("To", "to_warehouse", "Link", 120, "Warehouse")]
	return cols, rows


def _report_revenue_by_month(filters):
	from_date = filters.get("from_date") or add_days(nowdate(), -365)
	to_date = filters.get("to_date") or nowdate()
	rows = frappe.db.sql(
		"""
		SELECT DATE_FORMAT(posting_date,'%%Y-%%m') as month, COUNT(*) as invoices, SUM(grand_total) as revenue
		FROM `tabSales Invoice`
		WHERE docstatus=1 AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY month ORDER BY month
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	cols = [_col("Month", "month", "Data", 100), _col("Invoices", "invoices", "Int", 80), _col("Revenue", "revenue", "Currency", 120)]
	return cols, rows


def _report_payment_summary(filters):
	from_date = filters.get("from_date") or add_days(nowdate(), -30)
	to_date = filters.get("to_date") or nowdate()
	rows = frappe.db.sql(
		"""
		SELECT mode_of_payment as mode, COUNT(*) as count, SUM(paid_amount) as total
		FROM `tabPayment Entry`
		WHERE docstatus=1 AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY mode_of_payment
		ORDER BY total DESC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	cols = [_col("Mode", "mode", "Link", 120, "Mode of Payment"), _col("Count", "count", "Int", 80), _col("Total", "total", "Currency", 120)]
	return cols, rows


def _report_outstanding(filters):
	rows = frappe.db.sql(
		"""
		SELECT name as invoice, customer, due_date, outstanding_amount, posting_date
		FROM `tabSales Invoice`
		WHERE docstatus=1 AND outstanding_amount>0
		ORDER BY due_date
		""",
		as_dict=True,
	)
	cols = [_col("Invoice", "invoice", "Link", 140, "Sales Invoice"), _col("Customer", "customer", "Link", 140, "Customer"), _col("Due Date", "due_date", "Date", 110), _col("Outstanding", "outstanding_amount", "Currency", 120)]
	return cols, rows


def _report_customer_statement(filters):
	rows = frappe.db.sql(
		"""
		SELECT customer, COUNT(*) as invoices, SUM(grand_total) as billed, SUM(outstanding_amount) as outstanding
		FROM `tabSales Invoice`
		WHERE docstatus=1
		GROUP BY customer
		ORDER BY outstanding DESC
		""",
		as_dict=True,
	)
	cols = [_col("Customer", "customer", "Link", 140, "Customer"), _col("Invoices", "invoices", "Int", 80), _col("Billed", "billed", "Currency", 120), _col("Outstanding", "outstanding", "Currency", 120)]
	return cols, rows


# Register 12 reports

_register("Job Turnaround Time", "Garage Job Card", _report_job_turnaround, None)
_register("Jobs Completed", "Garage Job Card", _report_jobs_completed, None)
_register("Technician Productivity", "Time Log Entry", _report_technician_productivity, None)
_register("Repairs by Type", "Vehicle Inspection", _report_repairs_by_type, None)
_register("Parts Usage", "Consumed Part Entry", _report_parts_usage, None)
_register("Slow Moving Parts", "Item", _report_slow_moving, None)
_register("Stock Count Variance", "Bin", _report_stock_variance, None)
_register("Stock Transfers", "Stock Entry", _report_stock_transfers, None)
_register("Revenue by Month", "Sales Invoice", _report_revenue_by_month, None)
_register("Payment Summary", "Payment Entry", _report_payment_summary, None)
_register("Outstanding Receivables", "Sales Invoice", _report_outstanding, None)
_register("Customer Statement Summary", "Sales Invoice", _report_customer_statement, None)


@frappe.whitelist()
def run_report(report_name, filters=None):
	"""Thin wrapper: resolve Report by name, run with filters, return rows+columns."""
	_require_insights()
	if isinstance(filters, str):
		filters = frappe.parse_json(filters) or {}
	filters = filters or {}

	# Prefer in-code registry
	if report_name in REPORT_REGISTRY:
		cols, data = REPORT_REGISTRY[report_name]["handler"](filters)
		return {"report_name": report_name, "columns": cols, "result": data, "rows": data}

	# Fallback to DB Report (Standard/Script/Query)
	if not frappe.db.exists("Report", report_name):
		frappe.throw(_("Report {0} not found").format(report_name))

	# For Query Reports with `query`, we could execute, but we delegate to frappe's runner if available
	try:
		from frappe.desk.query_report import run as qr_run

		# qr_run expects report_name and filters
		result = qr_run(report_name, filters=filters)
		# frappe's run returns dict with columns/result
		if isinstance(result, dict):
			return {"report_name": report_name, "columns": result.get("columns"), "result": result.get("result"), "rows": result.get("result")}
		return {"report_name": report_name, "result": result}
	except Exception:
		frappe.throw(_("Failed to run report {0}").format(report_name))
