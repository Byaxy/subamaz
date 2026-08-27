# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


def add_timeline_entry(service_order, description, event_type="System", visible=True):
	"""Append a timeline entry to a Service Order."""
	if isinstance(service_order, str):
		doc = frappe.get_doc("Service Order", service_order)
	else:
		doc = service_order
	doc.append(
		"timeline",
		{
			"timestamp": now_datetime(),
			"user": frappe.session.user,
			"event_type": event_type,
			"description": description,
			"visible_to_customer": 1 if visible else 0,
		},
	)
	doc.save(ignore_permissions=True)
	return doc


def recompute_rollup(service_order):
	"""Recompute financial rollups from linked Job Cards. Guarded for phase 06 (no Job Card yet)."""
	if isinstance(service_order, str):
		doc = frappe.get_doc("Service Order", service_order)
	else:
		doc = service_order

	if not frappe.db.exists("DocType", "Job Card"):
		_update_estimated_total(doc)
		return doc

	job_cards = frappe.get_all(
		"Job Card",
		filters={"service_order": doc.name},
		fields=["name", "estimated_cost", "completion_percent"],
	)
	if not job_cards:
		_update_estimated_total(doc)
		return doc

	total_estimated = 0
	total_actual_labour = 0
	total_actual_parts = 0
	weighted_completion = 0
	total_weight = 0

	for jc in job_cards:
		estimated = jc.get("estimated_cost") or 0
		total_estimated += estimated
		jc_name = jc.get("name")
		# Time logs and consumed parts are phase 07 — try to fetch if doctypes exist
		if frappe.db.exists("DocType", "Job Card Time Log"):
			time_logs = frappe.get_all(
				"Job Card Time Log",
				filters={"parent": jc_name},
				fields=["labour_cost"],
			)
			for tl in time_logs:
				total_actual_labour += tl.get("labour_cost") or 0
		if frappe.db.exists("DocType", "Job Card Consumed Part"):
			parts = frappe.get_all(
				"Job Card Consumed Part",
				filters={"parent": jc_name},
				fields=["amount"],
			)
			for p in parts:
				total_actual_parts += p.get("amount") or 0

		comp = jc.get("completion_percent") or 0
		weighted_completion += comp * (estimated or 1)
		total_weight += estimated or 1

	doc.estimated_labour = total_estimated
	doc.estimated_total = total_estimated + (doc.estimated_parts or 0)
	doc.actual_labour = total_actual_labour
	doc.actual_parts = total_actual_parts
	doc.actual_total = total_actual_labour + total_actual_parts
	doc.completion_percent = (weighted_completion / total_weight) if total_weight else 0
	doc.db_update()
	return doc


def _update_estimated_total(doc):
	"""Fallback when no Job Cards exist — just ensure totals are consistent."""
	doc.estimated_total = (doc.estimated_labour or 0) + (doc.estimated_parts or 0)
	doc.actual_total = (doc.actual_labour or 0) + (doc.actual_parts or 0)
	doc.db_update()


def on_job_card_update(doc, method=None):
	"""Hook for Job Card.on_update — recompute rollup on linked Service Order."""
	service_order = getattr(doc, "service_order", None)
	if not service_order:
		return
	if not frappe.db.exists("DocType", "Service Order"):
		return
	if not frappe.db.exists("Service Order", service_order):
		return
	try:
		recompute_rollup(service_order)
	except Exception:
		frappe.log_error(title="Service Order rollup failed", message=frappe.get_traceback())


class ServiceOrder(Document):
	def validate(self):
		self._autofill_from_reception()
		self._compute_estimated_total()

	def _autofill_from_reception(self):
		if not self.vehicle_reception:
			return
		reception = frappe.db.get_value(
			"Vehicle Reception",
			self.vehicle_reception,
			["customer", "vehicle", "customer_complaint"],
			as_dict=True,
		)
		if not reception:
			return
		if not self.customer and reception.customer:
			self.customer = reception.customer
		if not self.vehicle and reception.vehicle:
			self.vehicle = reception.vehicle
		if not self.customer_complaint and reception.customer_complaint:
			self.customer_complaint = reception.customer_complaint

	def _compute_estimated_total(self):
		self.estimated_total = (self.estimated_labour or 0) + (self.estimated_parts or 0)
		self.actual_total = (self.actual_labour or 0) + (self.actual_parts or 0)

	def on_submit(self):
		self._link_vehicle()

	def _link_vehicle(self):
		if self.vehicle:
			frappe.db.set_value("Garage Vehicle", self.vehicle, "current_service_order", self.name)
			# also update status to indicate service started — best effort
			try:
				frappe.db.set_value("Garage Vehicle", self.vehicle, "current_status", "Waiting Approval")
			except Exception:
				pass

	def on_update_after_submit(self):
		self._ensure_project_and_quotation()

	def _ensure_project_and_quotation(self):
		try:
			self._ensure_project()
		except Exception:
			frappe.log_error(title="Service Order auto-Project failed", message=frappe.get_traceback())
		try:
			self._ensure_quotation()
		except Exception:
			frappe.log_error(title="Service Order auto-Quotation failed", message=frappe.get_traceback())

	def _ensure_project(self):
		if self.project:
			return
		if not frappe.db.exists("DocType", "Project"):
			return
		threshold_days = frappe.db.get_single_value("Garage Settings", "project_duration_threshold_days") or 14
		cost_threshold = frappe.db.get_single_value("Garage Settings", "project_cost_threshold") or 5000000

		needs_project = False
		if self.expected_finish and self.opening_date:
			from frappe.utils import date_diff

			try:
				days = date_diff(self.expected_finish, self.opening_date)
				if days > int(threshold_days):
					needs_project = True
			except Exception:
				pass
		if (self.estimated_total or 0) > float(cost_threshold):
			needs_project = True

		if not needs_project:
			return

		company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
			"Company", {}, "name"
		)
		project = frappe.get_doc(
			{
				"doctype": "Project",
				"project_name": self.name,
				"customer": self.customer,
				"expected_start_date": self.opening_date,
				"expected_end_date": self.expected_finish,
				"company": company,
				"status": "Open",
			}
		)
		project.insert(ignore_permissions=True)
		frappe.db.set_value("Service Order", self.name, "project", project.name)
		self.project = project.name
		add_timeline_entry(self, f"Project {project.name} auto-created", "System", visible=False)

	def _ensure_quotation(self):
		if self.quotation:
			return
		if not frappe.db.exists("DocType", "Quotation"):
			return
		if not (self.estimated_total or 0):
			return

		company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
			"Company", {}, "name"
		)
		customer_name = frappe.db.get_value("Customer", self.customer, "customer_name") or self.customer
		item_code = frappe.db.get_value("Item", {}, "item_code")
		if not item_code:
			# fallback: try to create a generic service item
			try:
				item = frappe.get_doc(
					{
						"doctype": "Item",
						"item_code": "Garage Service",
						"item_name": "Garage Service",
						"item_group": frappe.db.get_value("Item Group", {}, "name") or "Services",
						"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
						"is_stock_item": 0,
					}
				)
				item.insert(ignore_permissions=True)
				item_code = item.name
			except Exception:
				item_code = None
		items = []
		if item_code:
			items = [{"item_code": item_code, "qty": 1, "rate": float(self.estimated_total or 0)}]
		quotation = frappe.get_doc(
			{
				"doctype": "Quotation",
				"quotation_to": "Customer",
				"party_name": self.customer,
				"customer_name": customer_name,
				"company": company,
				"transaction_date": self.opening_date,
				"items": items,
				"order_type": "Sales",
			}
		)
		quotation.insert(ignore_permissions=True)
		frappe.db.set_value("Service Order", self.name, "quotation", quotation.name)
		self.quotation = quotation.name
		add_timeline_entry(self, f"Quotation {quotation.name} auto-created (draft)", "System", visible=False)
