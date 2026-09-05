# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _


@frappe.whitelist()
def global_search(query):
	"""Ranked typed results for the Garage Admin global search bar.

	Searches Garage Vehicle (registration/VIN/customer), Customer, Service Order,
	Garage Job Card, Sales Invoice. Returns list of {doctype, name, label, route}.
	"""
	if not query or not query.strip():
		return []
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	query = query.strip()
	like = f"%{query}%"
	results = []

	# Garage Vehicle — registration, vin, customer name
	try:
		vehicles = frappe.get_all(
			"Garage Vehicle",
			filters=[
				["Garage Vehicle", "registration_number", "like", like],
			],
			fields=["name", "registration_number", "vin", "customer"],
			limit=5,
		)
		# also vin fallback if no results
		if not vehicles:
			vehicles = frappe.get_all(
				"Garage Vehicle",
				filters=[["Garage Vehicle", "vin", "like", like]],
				fields=["name", "registration_number", "vin", "customer"],
				limit=5,
			)
		for v in vehicles:
			results.append(
				{
					"doctype": "Garage Vehicle",
					"name": v["name"],
					"label": v["registration_number"] or v["name"],
					"description": v["vin"] or v["customer"] or "",
					"type": "Vehicle",
					"route": f"/vehicles/{v['name']}",
				}
			)
	except Exception:
		pass

	# Customer
	try:
		customers = frappe.get_all(
			"Customer",
			filters=[["Customer", "customer_name", "like", like]],
			fields=["name", "customer_name"],
			limit=5,
		)
		for c in customers:
			results.append(
				{
					"doctype": "Customer",
					"name": c["name"],
					"label": c["customer_name"] or c["name"],
					"description": "Customer",
					"type": "Customer",
					"route": f"/customers/{c['name']}",
				}
			)
	except Exception:
		pass

	# Service Order
	try:
		sos = frappe.get_all(
			"Service Order",
			filters=[["Service Order", "name", "like", like]],
			fields=["name", "customer", "vehicle", "status"],
			limit=5,
		)
		if not sos:
			sos = frappe.get_all(
				"Service Order",
				filters=[["Service Order", "customer", "like", like]],
				fields=["name", "customer", "vehicle", "status"],
				limit=5,
			)
		for s in sos:
			results.append(
				{
					"doctype": "Service Order",
					"name": s["name"],
					"label": s["name"],
					"description": f"{s['customer'] or ''} • {s['status'] or ''}",
					"type": "Service Order",
					"route": f"/service/orders/{s['name']}",
				}
			)
	except Exception:
		pass

	# Garage Job Card
	try:
		jcs = frappe.get_all(
			"Garage Job Card",
			filters=[["Garage Job Card", "name", "like", like]],
			fields=["name", "service_order", "status"],
			limit=5,
		)
		for j in jcs:
			results.append(
				{
					"doctype": "Garage Job Card",
					"name": j["name"],
					"label": j["name"],
					"description": j["status"] or "",
					"type": "Job Card",
					"route": f"/service/job-cards/{j['name']}",
				}
			)
	except Exception:
		pass

	# Sales Invoice
	try:
		invs = frappe.get_all(
			"Sales Invoice",
			filters=[["Sales Invoice", "name", "like", like]],
			fields=["name", "customer", "status"],
			limit=5,
		)
		if not invs:
			invs = frappe.get_all(
				"Sales Invoice",
				filters=[["Sales Invoice", "customer", "like", like]],
				fields=["name", "customer", "status"],
				limit=5,
			)
		for inv in invs:
			results.append(
				{
					"doctype": "Sales Invoice",
					"name": inv["name"],
					"label": inv["name"],
					"description": inv["customer"] or inv["status"] or "",
					"type": "Invoice",
					"route": f"/records/invoices/{inv['name']}",
				}
			)
	except Exception:
		pass

	return results[:20]
