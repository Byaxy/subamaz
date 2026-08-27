# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, has_common, now_datetime

ALLOWED_TRANSITIONS = {
	"Draft": ["Assigned", "Cancelled"],
	"Assigned": ["Accepted", "Cancelled"],
	"Accepted": ["Working", "Cancelled"],
	"Working": ["Paused", "Waiting Parts", "Waiting Approval", "Ready QA", "Completed", "Cancelled"],
	"Paused": ["Working", "Waiting Parts", "Waiting Approval", "Cancelled"],
	"Waiting Parts": ["Working", "Paused", "Waiting Approval", "Cancelled"],
	"Waiting Approval": ["Working", "Paused", "Waiting Parts", "Cancelled"],
	"Ready QA": ["Completed", "Cancelled"],
	"Completed": ["Cancelled"],
	"Cancelled": [],
}

STATUS_HOURS_DEFAULT_FALLBACK = 0


def _get_previous_status(name):
	if not name:
		return None
	return frappe.db.get_value("Garage Job Card", name, "status")


class GarageJobCard(Document):
	def validate(self):
		self._validate_status_transition()
		self._recompute_child_amounts()
		self._recompute_totals()

	def _validate_status_transition(self):
		if self.is_new():
			return
		prev = _get_previous_status(self.name)
		if not prev or prev == self.status:
			return
		if self.status == "Cancelled":
			if not has_common(["Garage Manager", "System Manager"], frappe.get_roles()):
				frappe.throw(_("Only Garage Manager can cancel a Garage Job Card"), frappe.PermissionError)
			return
		allowed = ALLOWED_TRANSITIONS.get(prev, [])
		if self.status not in allowed:
			frappe.throw(
				_("Invalid status transition from {0} to {1}").format(prev, self.status),
				frappe.ValidationError,
			)

	def _recompute_child_amounts(self):
		for row in self.time_logs or []:
			if row.hours is None or row.hours == 0:
				if row.started_at and row.finished_at:
					try:
						from frappe.utils import time_diff_in_hours

						row.hours = time_diff_in_hours(row.finished_at, row.started_at)
					except Exception:
						row.hours = 0
			if row.hourly_rate is None:
				# default from department
				if self.department:
					row.hourly_rate = frappe.db.get_value(
						"Garage Department", self.department, "default_hourly_rate"
					) or 0
				else:
					row.hourly_rate = 0
			row.labour_cost = flt(row.hours) * flt(row.hourly_rate)

		for row in self.consumed_parts or []:
			row.amount = flt(row.qty) * flt(row.rate)
			if not row.rate and row.item_code:
				row.rate = frappe.db.get_value("Item", row.item_code, "valuation_rate") or row.rate or 0
				row.amount = flt(row.qty) * flt(row.rate)

	def _recompute_totals(self):
		total_hours = sum(flt(r.hours) for r in (self.time_logs or []))
		total_labour = sum(flt(r.labour_cost) for r in (self.time_logs or []))
		total_parts = sum(flt(r.amount) for r in (self.consumed_parts or []))
		self.actual_hours = total_hours
		self.actual_cost = total_labour + total_parts

	def before_submit(self):
		if self.status not in ("Completed", "Ready QA"):
			# allow submit from Working/Paused etc via complete flow — set to Completed
			self.status = "Completed"

	def on_update(self):
		self._trigger_so_rollup()

	def on_submit(self):
		self._trigger_so_rollup()
		self._advance_service_order_if_last()

	def _trigger_so_rollup(self):
		if not self.service_order:
			return
		try:
			from subamaz.subamaz.doctype.service_order.service_order import recompute_rollup

			recompute_rollup(self.service_order)
		except Exception:
			frappe.log_error(title="Garage Job Card SO rollup failed", message=frappe.get_traceback())

	def _advance_service_order_if_last(self):
		if not self.service_order:
			return
		if not frappe.db.exists("DocType", "Service Order"):
			return
		try:
			siblings = frappe.get_all(
				"Garage Job Card",
				filters={"service_order": self.service_order, "docstatus": ["<", 2]},
				fields=["name", "status", "docstatus"],
			)
			all_done = all(s.status == "Completed" and s.docstatus == 1 for s in siblings)
			if not all_done:
				return
			so = frappe.get_doc("Service Order", self.service_order)
			# If SO is still in In Progress, move to Quality Check
			if so.status == "In Progress":
				frappe.db.set_value("Service Order", so.name, "status", "Quality Check")
				so.reload()
				try:
					from subamaz.subamaz.doctype.service_order.service_order import add_timeline_entry

					add_timeline_entry(so, "All Job Cards completed — moved to Quality Check", "System")
				except Exception:
					pass
		except Exception:
			frappe.log_error(title="Garage Job Card SO advance failed", message=frappe.get_traceback())

	def get_dashboard_data(self):
		return {
			"fieldname": "job_card",
			"transactions": [
				{"label": "Repair Tasks", "items": ["Repair Task"]},
				{"label": "Stock", "items": ["Stock Entry"]},
			],
		}
