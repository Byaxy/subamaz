# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.model.document import Document


class VehicleDelivery(Document):
	def on_submit(self):
		self._close_repair_tasks()
		self._complete_project()
		self._create_sales_invoice()
		self._set_vehicle_available()
		self._append_timeline()
		self._enqueue_reminder()
		self._enqueue_survey()

	def _close_repair_tasks(self):
		# Find all Repair Tasks linked to Garage Job Cards of this Service Order
		if not self.service_order:
			return
		job_cards = frappe.get_all(
			"Garage Job Card", filters={"service_order": self.service_order}, pluck="name"
		)
		if not job_cards:
			return
		tasks = frappe.get_all(
			"Repair Task",
			filters={"job_card": ["in", job_cards], "status": ["!=", "Completed"]},
			fields=["name"],
		)
		for t in tasks:
			try:
				frappe.db.set_value("Repair Task", t.name, "status", "Completed")
				frappe.db.set_value("Repair Task", t.name, "finished_at", frappe.utils.now_datetime())
			except Exception:
				frappe.log_error(title="Vehicle Delivery close task failed", message=frappe.get_traceback())

	def _complete_project(self):
		so = None
		try:
			so = frappe.get_doc("Service Order", self.service_order)
		except Exception:
			return
		if not so or not so.project:
			return
		if not frappe.db.exists("Project", so.project):
			return
		try:
			frappe.db.set_value("Project", so.project, "status", "Completed")
		except Exception:
			frappe.log_error(title="Vehicle Delivery project complete failed", message=frappe.get_traceback())

	def _create_sales_invoice(self):
		so = None
		try:
			so = frappe.get_doc("Service Order", self.service_order)
		except Exception:
			return
		if not so:
			return
		if so.sales_invoice and frappe.db.exists("Sales Invoice", so.sales_invoice):
			return
		if not frappe.db.exists("DocType", "Sales Invoice"):
			return
		try:
			company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
				"Company", {}, "name"
			)
			customer = so.customer or self.customer
			# Try to create invoice from quotation if exists, else minimal
			items = []
			if so.quotation and frappe.db.exists("Quotation", so.quotation):
				q = frappe.get_doc("Quotation", so.quotation)
				for qi in q.items or []:
					items.append({"item_code": qi.item_code, "qty": qi.qty, "rate": qi.rate})
			if not items:
				item_code = frappe.db.get_value("Item", {}, "item_code")
				if not item_code:
					# create fallback item
					item = frappe.get_doc(
						{
							"doctype": "Item",
							"item_code": "Garage Service",
							"item_name": "Garage Service",
							"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
							"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
							"is_stock_item": 0,
						}
					)
					item.insert(ignore_permissions=True)
					item_code = item.name
				rate = float(so.estimated_total or 0) or 1000
				items = [{"item_code": item_code, "qty": 1, "rate": rate}]
			invoice = frappe.get_doc(
				{
					"doctype": "Sales Invoice",
					"customer": customer,
					"company": company,
					"items": items,
				}
			)
			invoice.insert(ignore_permissions=True)
			# Do not submit automatically — leave draft for now, but try submit if possible
			try:
				invoice.submit()
			except Exception:
				pass
			frappe.db.set_value("Service Order", so.name, "sales_invoice", invoice.name)
		except Exception:
			frappe.log_error(title="Vehicle Delivery invoice create failed", message=frappe.get_traceback())

	def _set_vehicle_available(self):
		vehicle = self.vehicle
		if not vehicle:
			try:
				so = frappe.get_doc("Service Order", self.service_order)
				vehicle = so.vehicle
			except Exception:
				vehicle = None
		if vehicle:
			try:
				frappe.db.set_value("Garage Vehicle", vehicle, "current_status", "Available")
				frappe.db.set_value("Garage Vehicle", vehicle, "current_service_order", "")
			except Exception:
				frappe.log_error(title="Vehicle Delivery set vehicle failed", message=frappe.get_traceback())

	def _append_timeline(self):
		try:
			if not frappe.db.exists("DocType", "Service Timeline Entry"):
				return
			from subamaz.subamaz.doctype.service_order.service_order import add_timeline_entry

			add_timeline_entry(
				self.service_order, f"Vehicle {self.vehicle} delivered via {self.name}", "System", visible=True
			)
		except Exception:
			frappe.log_error(title="Vehicle Delivery timeline failed", message=frappe.get_traceback())

	def _enqueue_reminder(self):
		try:
			frappe.enqueue(
				"subamaz.subamaz.doctype.vehicle_delivery.vehicle_delivery.enqueue_reminder",
				service_order=self.service_order,
				vehicle=self.vehicle,
				enqueue_after_commit=True,
			)
		except Exception:
			frappe.log_error(title="Vehicle Delivery enqueue reminder failed", message=frappe.get_traceback())

	def _enqueue_survey(self):
		try:
			if not frappe.db.get_single_value("Garage Settings", "enable_satisfaction_survey"):
				return
			frappe.enqueue(
				"subamaz.subamaz.doctype.vehicle_delivery.vehicle_delivery.enqueue_survey",
				service_order=self.service_order,
				vehicle=self.vehicle,
				enqueue_after_commit=True,
			)
		except Exception:
			frappe.log_error(title="Vehicle Delivery enqueue survey failed", message=frappe.get_traceback())


def enqueue_reminder(service_order, vehicle):
	# stub for background job — actual email scheduling would go here
	frappe.logger().info(f"Reminder enqueued for {service_order} vehicle {vehicle}")


def enqueue_survey(service_order, vehicle):
	frappe.logger().info(f"Survey enqueued for {service_order} vehicle {vehicle}")
