# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _

from subamaz.api.access_control import has_capability


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


def _require_capability(capability):
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not has_capability(frappe.session.user, capability):
		frappe.throw(_("Not permitted — missing {0}").format(capability), frappe.PermissionError)


@frappe.whitelist()
def get_vehicle_history(vehicle):
	"""Full history for a vehicle across receptions, inspections, orders, job cards, deliveries."""
	_require_capability("module:customers_vehicles")
	if not vehicle or not frappe.db.exists("Garage Vehicle", vehicle):
		frappe.throw(_("Vehicle {0} not found").format(vehicle))
	history = []
	# Receptions
	for r in frappe.get_all(
		"Vehicle Reception",
		filters={"vehicle": vehicle},
		fields=["name", "creation", "reception_date", "customer", "status", "customer_complaint"],
		order_by="creation asc",
	):
		history.append(
			{
				"doctype": "Vehicle Reception",
				"name": r["name"],
				"date": str(r.get("reception_date") or r.get("creation")),
				"title": f"Reception {r['name']}",
				"description": r.get("customer_complaint") or r.get("status") or "",
				"visible_to_customer": 1,
			}
		)
	# Inspections
	for r in frappe.get_all(
		"Vehicle Inspection",
		filters={"vehicle": vehicle},
		fields=["name", "creation", "inspection_date", "inspection_result", "recommendation"],
		order_by="creation asc",
	):
		history.append(
			{
				"doctype": "Vehicle Inspection",
				"name": r["name"],
				"date": str(r.get("inspection_date") or r.get("creation")),
				"title": f"Inspection {r['name']}",
				"description": f"{r.get('inspection_result') or ''} — {r.get('recommendation') or ''}",
				"visible_to_customer": 0,
			}
		)
	# Service Orders
	for r in frappe.get_all(
		"Service Order",
		filters={"vehicle": vehicle},
		fields=["name", "creation", "opening_date", "status", "customer_complaint"],
		order_by="creation asc",
	):
		history.append(
			{
				"doctype": "Service Order",
				"name": r["name"],
				"date": str(r.get("opening_date") or r.get("creation")),
				"title": f"Service Order {r['name']}",
				"description": r.get("status") or "",
				"visible_to_customer": 1,
			}
		)
		# Timeline entries for this SO (customer-visible vs internal)
		try:
			so = frappe.get_doc("Service Order", r["name"])
			for tl in so.timeline or []:
				history.append(
					{
						"doctype": "Service Timeline Entry",
						"name": f"{r['name']}-{tl.timestamp}",
						"date": str(tl.timestamp),
						"title": f"Timeline {tl.event_type}",
						"description": tl.description or "",
						"visible_to_customer": 1 if tl.visible_to_customer else 0,
						"parent": r["name"],
					}
				)
		except Exception:
			pass
	# Job Cards via Service Orders
	so_names = frappe.get_all("Service Order", filters={"vehicle": vehicle}, pluck="name")
	if so_names:
		for r in frappe.get_all(
			"Garage Job Card",
			filters={"service_order": ["in", so_names]},
			fields=["name", "creation", "service_order", "status", "department"],
			order_by="creation asc",
		):
			history.append(
				{
					"doctype": "Garage Job Card",
					"name": r["name"],
					"date": str(r["creation"]),
					"title": f"Job Card {r['name']}",
					"description": f"{r['department'] or ''} — {r['status']}",
					"visible_to_customer": 0,
				}
			)
	# Deliveries
	for r in frappe.get_all(
		"Vehicle Delivery",
		filters={"vehicle": vehicle},
		fields=["name", "creation", "delivery_date", "service_order"],
		order_by="creation asc",
	):
		history.append(
			{
				"doctype": "Vehicle Delivery",
				"name": r["name"],
				"date": str(r.get("delivery_date") or r.get("creation")),
				"title": f"Delivery {r['name']}",
				"description": r.get("service_order") or "",
				"visible_to_customer": 1,
			}
		)
	# Sort by date
	try:
		history.sort(key=lambda x: x["date"] or "")
	except Exception:
		pass
	return history


@frappe.whitelist()
def get_stock_status(warehouse=None):
	"""Stock balances with valuation and reorder levels — for PARTS & STOCK."""
	_require_capability("module:parts_stock")
	filters = {}
	if warehouse:
		filters["warehouse"] = warehouse
	bins = frappe.get_all("Bin", filters=filters, fields=["item_code", "warehouse", "actual_qty", "valuation_rate", "stock_value"], limit=500)
	# Enrich with Item reorder levels
	for b in bins:
		try:
			item = frappe.get_doc("Item", b["item_code"])
			reorder = 0
			for row in item.reorder_levels or []:
				if not warehouse or row.warehouse == warehouse:
					reorder = float(row.warehouse_reorder_level or 0)
					break
			b["reorder_level"] = reorder
			b["item_name"] = item.item_name
			b["is_stock_item"] = item.is_stock_item
		except Exception:
			b["reorder_level"] = 0
	return bins


@frappe.whitelist()
def get_restock_preview(warehouse=None):
	"""Preview low-stock grouped by supplier → draft POs.

	Returns {groups: [{supplier, items: [{item_code, qty_needed, valuation_rate}]}], low_items: [...]}
	"""
	_require_capability("module:parts_stock")
	bins = frappe.get_all("Bin", filters={"warehouse": warehouse} if warehouse else {}, fields=["item_code", "warehouse", "actual_qty"], limit=500)
	low_items = []
	for b in bins:
		try:
			item = frappe.get_doc("Item", b["item_code"])
			if not item.is_stock_item:
				continue
			reorder_level = 0
			reorder_qty = 0
			for row in item.reorder_levels or []:
				if not warehouse or row.warehouse == warehouse:
					reorder_level = float(row.warehouse_reorder_level or 0)
					reorder_qty = float(row.warehouse_reorder_qty or 0)
					break
			if reorder_level and float(b["actual_qty"] or 0) < reorder_level:
				# Determine supplier (first Item Supplier)
				supplier = None
				if item.supplier_items:
					supplier = item.supplier_items[0].supplier
				# Fallback to Item's default supplier field if exists
				if not supplier:
					supplier = getattr(item, "supplier", None)
				if not supplier:
					supplier = "No Supplier"
				needed = max(reorder_qty or (reorder_level - float(b["actual_qty"] or 0)), 1)
				low_items.append(
					{
						"item_code": b["item_code"],
						"item_name": item.item_name,
						"warehouse": b["warehouse"],
						"actual_qty": float(b["actual_qty"] or 0),
						"reorder_level": reorder_level,
						"reorder_qty": reorder_qty,
						"qty_needed": needed,
						"valuation_rate": frappe.db.get_value("Item", b["item_code"], "valuation_rate") or 0,
						"supplier": supplier,
					}
				)
		except Exception:
			continue
	# Group by supplier
	groups = {}
	for it in low_items:
		groups.setdefault(it["supplier"], []).append(it)
	grouped = [{"supplier": k, "items": v, "total_items": len(v)} for k, v in groups.items()]
	return {"low_items": low_items, "groups": grouped, "count": len(low_items)}


@frappe.whitelist()
def get_procurement_counts():
	_require_capability("module:procurement")
	return {
		"supplier_quotations": frappe.db.count("Supplier Quotation", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Supplier Quotation") else 0,
		"purchase_orders": frappe.db.count("Purchase Order", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Purchase Order") else 0,
		"purchase_invoices": frappe.db.count("Purchase Invoice", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Purchase Invoice") else 0,
		"purchase_receipts": frappe.db.count("Purchase Receipt", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Purchase Receipt") else 0,
	}


@frappe.whitelist()
def get_money_counts():
	_require_capability("module:records_money")
	return {
		"invoices": frappe.db.count("Sales Invoice", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Sales Invoice") else 0,
		"payments": frappe.db.count("Payment Entry", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Payment Entry") else 0,
		"quotations": frappe.db.count("Quotation", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Quotation") else 0,
		"petty_cash": frappe.db.count("Petty Cash Log", {"docstatus": ["<", 2]}) if frappe.db.exists("DocType", "Petty Cash Log") else 0,
	}


@frappe.whitelist()
def apply_invoice_discount(invoice, discount_amount):
	_require_capability("action:apply_invoice_discount")
	if not frappe.db.exists("Sales Invoice", invoice):
		frappe.throw(_("Sales Invoice {0} not found").format(invoice))
	try:
		frappe.db.set_value("Sales Invoice", invoice, "discount_amount", float(discount_amount), update_modified=False)
	except Exception:
		frappe.log_error(title="apply_invoice_discount failed", message=frappe.get_traceback())
		frappe.throw(_("Failed to apply discount"))
	return {"invoice": invoice, "discount": float(discount_amount)}


@frappe.whitelist()
def void_invoice(invoice):
	_require_capability("action:void_invoice")
	if not frappe.db.exists("Sales Invoice", invoice):
		frappe.throw(_("Sales Invoice {0} not found").format(invoice))
	doc = frappe.get_doc("Sales Invoice", invoice)
	if doc.docstatus == 2:
		return {"invoice": invoice, "status": "Already Cancelled"}
	try:
		doc.cancel()
	except Exception:
		frappe.db.set_value("Sales Invoice", invoice, "status", "Cancelled")
	return {"invoice": invoice, "status": "Cancelled"}


@frappe.whitelist()
def approve_credit_sale(invoice):
	_require_capability("action:approve_credit_sale")
	if not frappe.db.exists("Sales Invoice", invoice):
		frappe.throw(_("Sales Invoice {0} not found").format(invoice))
	frappe.db.set_value("Sales Invoice", invoice, "status", "Overdue")
	return {"invoice": invoice, "approved": True}


@frappe.whitelist()
def create_petty_cash(amount, description, expense_type=None, paid_by=None):
	_require_capability("action:record_petty_cash")
	if not frappe.db.exists("DocType", "Petty Cash Log"):
		frappe.throw(_("Petty Cash Log not found"))
	doc = frappe.get_doc(
		{
			"doctype": "Petty Cash Log",
			"posting_date": frappe.utils.today(),
			"amount": float(amount),
			"description": description,
			"expense_type": expense_type or "Misc",
			"paid_by": paid_by,
			"status": "Draft",
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}
