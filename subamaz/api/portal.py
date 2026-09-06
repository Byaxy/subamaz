# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _


def _get_customer_for_user(user=None):
	user = user or frappe.session.user
	if user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	# Find Contact linked to user
	contact = frappe.db.get_value("Contact", {"user": user}, "name")
	if not contact:
		# Try Dynamic Link
		contact = frappe.db.get_value("Dynamic Link", {"link_doctype": "Contact", "link_name": user}, "parent")
		# Alternative: Contact Email (support both top-level email_id and child table)
		if not contact:
			email = frappe.db.get_value("User", user, "email")
			if email:
				contact = frappe.db.get_value("Contact", {"email_id": email}, "name")
				if not contact:
					contact = frappe.db.get_value("Contact Email", {"email_id": email}, "parent")
	if not contact:
		frappe.throw(_("No linked Customer found for user {0}").format(user), frappe.ValidationError)
	# Find Customer linked to Contact via Dynamic Link
	customer = frappe.db.get_value("Dynamic Link", {"parent": contact, "parenttype": "Contact", "link_doctype": "Customer"}, "link_name")
	if not customer:
		# Try Contact's customer field? fallback: first Customer linked to Contact's email?
		customer = frappe.db.get_value("Customer", {"customer_name": frappe.db.get_value("Contact", contact, "first_name")}, "name")
	if not customer:
		frappe.throw(_("No linked Customer found for Contact {0}").format(contact), frappe.ValidationError)
	return customer, contact


def _filter_owned(vehicles):
	# Helper to ensure we only return owned vehicles
	return vehicles


@frappe.whitelist()
def get_my_vehicles():
	customer, _contact = _get_customer_for_user()
	vehicles = frappe.get_all(
		"Garage Vehicle",
		filters={"customer": customer},
		fields=["name", "registration_number", "vin", "make", "model", "customer", "current_status", "current_mileage", "current_service_order"],
	)
	return vehicles


@frappe.whitelist()
def get_vehicle_detail(vehicle):
	customer, _contact = _get_customer_for_user()
	doc = frappe.get_doc("Garage Vehicle", vehicle)
	if doc.customer != customer:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc.as_dict()


@frappe.whitelist()
def get_service_order_progress(name):
	customer, _contact = _get_customer_for_user()
	doc = frappe.get_doc("Service Order", name)
	if doc.customer != customer:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	# Return aggregated progress — never raw Job Card data
	return {
		"name": doc.name,
		"status": doc.status,
		"completion_percent": doc.completion_percent,
		"estimated_total": doc.estimated_total,
		"actual_total": doc.actual_total,
		"opening_date": str(doc.opening_date) if doc.opening_date else None,
		"expected_finish": str(doc.expected_finish) if doc.expected_finish else None,
		"customer_complaint": doc.customer_complaint,
	}


@frappe.whitelist()
def get_customer_timeline(service_order=None):
	customer, _contact = _get_customer_for_user()
	filters = {"customer": customer}
	if service_order:
		# Ensure owned
		so = frappe.get_doc("Service Order", service_order)
		if so.customer != customer:
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		filters = {"name": service_order}
	orders = frappe.get_all("Service Order", filters=filters, fields=["name"])
	result = []
	for o in orders:
		doc = frappe.get_doc("Service Order", o.name)
		for tl in doc.timeline or []:
			if tl.visible_to_customer:
				result.append(
					{
						"service_order": doc.name,
						"timestamp": str(tl.timestamp),
						"event_type": tl.event_type,
						"description": tl.description,
						"visible_to_customer": 1,
					}
				)
	return result


@frappe.whitelist()
def get_quotation(name):
	customer, _contact = _get_customer_for_user()
	doc = frappe.get_doc("Quotation", name)
	# Quotation party is customer
	if doc.party_name != customer and doc.customer_name != customer:
		# Fallback: check if customer matches
		if getattr(doc, "customer", None) != customer:
			frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc.as_dict()


@frappe.whitelist()
def approve_quotation(name, action="Approve"):
	customer, _contact = _get_customer_for_user()
	doc = frappe.get_doc("Quotation", name)
	if doc.party_name != customer and doc.customer_name != customer and getattr(doc, "customer", None) != customer:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if action == "Approve":
		# Update status and also update linked Service Order if exists
		try:
			doc.status = "Ordered"
			doc.save(ignore_permissions=True)
		except Exception:
			frappe.db.set_value("Quotation", name, "status", "Ordered")
		# Find Service Order linked via quotation
		so_name = frappe.db.get_value("Service Order", {"quotation": name}, "name")
		if so_name:
			try:
				frappe.db.set_value("Service Order", so_name, "status", "Waiting Customer")
			except Exception:
				pass
		return {"name": name, "status": "Approved"}
	else:
		try:
			doc.status = "Cancelled"
			doc.save(ignore_permissions=True)
		except Exception:
			frappe.db.set_value("Quotation", name, "status", "Cancelled")
		return {"name": name, "status": "Rejected"}


@frappe.whitelist()
def get_my_invoices():
	customer, _contact = _get_customer_for_user()
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1},
		fields=["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"],
	)
	return invoices


@frappe.whitelist()
def get_service_history():
	customer, _contact = _get_customer_for_user()
	# Reuse vehicle history logic but for all vehicles of customer
	vehicles = frappe.get_all("Garage Vehicle", filters={"customer": customer}, pluck="name")
	history = []
	for v in vehicles:
		# Use admin's get_vehicle_history but we need to bypass capability check — instead directly query
		for r in frappe.get_all("Vehicle Reception", filters={"vehicle": v}, fields=["name", "creation", "customer_complaint"], order_by="creation asc"):
			history.append({"doctype": "Vehicle Reception", "name": r["name"], "date": str(r["creation"]), "title": f"Reception {r['name']}", "description": r.get("customer_complaint") or ""})
		for r in frappe.get_all("Service Order", filters={"vehicle": v}, fields=["name", "creation", "status"], order_by="creation asc"):
			history.append({"doctype": "Service Order", "name": r["name"], "date": str(r["creation"]), "title": f"Service Order {r['name']}", "description": r.get("status") or ""})
	return history


@frappe.whitelist()
def get_reception_record(name):
	customer, _contact = _get_customer_for_user()
	doc = frappe.get_doc("Vehicle Reception", name)
	if doc.customer != customer:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc.as_dict()
