# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


def _create_customer_with_contact(email):
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": f"Portal Cust {frappe.generate_hash(length=4)}"}).insert(ignore_permissions=True)
	contact = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": f"Portal {frappe.generate_hash(length=4)}",
			"email_ids": [{"email_id": email, "is_primary": 1}],
			"links": [{"link_doctype": "Customer", "link_name": customer.name}],
		}
	).insert(ignore_permissions=True)
	return customer, contact


def _create_website_user(email, customer=None):
	if frappe.db.exists("User", email):
		return email
	frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": "Portal",
			"send_welcome_email": 0,
			"user_type": "Website User",
		}
	).insert(ignore_permissions=True)
	if customer:
		contact_name = frappe.db.get_value("Contact Email", {"email_id": email}, "parent")
		if not contact_name:
			contact_name = frappe.db.get_value("Contact", {"email_id": email}, "name")
		if not contact_name:
			frappe.get_doc(
				{
					"doctype": "Contact",
					"first_name": "Portal",
					"email_ids": [{"email_id": email, "is_primary": 1}],
					"links": [{"link_doctype": "Customer", "link_name": customer}],
				}
			).insert(ignore_permissions=True)
	return email


def _create_vehicle(customer):
	return frappe.get_doc(
		{
			"doctype": "Garage Vehicle",
			"registration_number": f"P-{frappe.generate_hash(length=5)}",
			"vin": frappe.generate_hash(length=17),
			"customer": customer,
			"current_mileage": 10000,
		}
	).insert(ignore_permissions=True)


def _create_employee():
	return frappe.get_doc(
		{
			"doctype": "Employee",
			"first_name": "PortalEmp",
			"last_name": frappe.generate_hash(length=4),
			"company": frappe.db.get_value("Company", {}, "name"),
			"gender": "Male",
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2020-01-01",
		}
	).insert(ignore_permissions=True)


def _create_reception(customer, vehicle, employee):
	doc = frappe.get_doc(
		{
			"doctype": "Vehicle Reception",
			"customer": customer,
			"vehicle": vehicle,
			"reception_advisor": employee,
			"customer_complaint": "Portal test complaint",
			"terms_accepted": 1,
			"photos": [
				{"photo": "/files/front.jpg", "photo_type": "Front"},
				{"photo": "/files/rear.jpg", "photo_type": "Rear"},
				{"photo": "/files/interior.jpg", "photo_type": "Interior"},
				{"photo": "/files/dashboard.jpg", "photo_type": "Dashboard"},
			],
		}
	).insert(ignore_permissions=True)
	doc.submit()
	return doc


def _create_service_order(customer, vehicle, reception, quotation=None):
	doc = frappe.get_doc(
		{
			"doctype": "Service Order",
			"customer": customer,
			"vehicle": vehicle,
			"vehicle_reception": reception.name,
			"opening_date": frappe.utils.today(),
			"quotation": quotation,
		}
	).insert(ignore_permissions=True)
	doc.submit()
	return doc


def _create_quotation(customer):
	company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {}, "name")
	customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
	item_code = frappe.db.get_value("Item", {}, "item_code")
	if not item_code:
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"PortalItem-{frappe.generate_hash(length=4)}",
				"item_name": "Portal Item",
				"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
				"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
				"is_stock_item": 0,
			}
		).insert(ignore_permissions=True)
		item_code = item.name
	quotation = frappe.get_doc(
		{
			"doctype": "Quotation",
			"quotation_to": "Customer",
			"party_name": customer,
			"customer_name": customer_name,
			"company": company,
			"transaction_date": frappe.utils.today(),
			"order_type": "Sales",
			"items": [{"item_code": item_code, "qty": 1, "rate": 10000}],
		}
	).insert(ignore_permissions=True)
	return quotation


class TestPortalAPI(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.employee = _create_employee()

	def test_ownership_filter(self):
		email_a = f"portal.a.{frappe.generate_hash(length=4)}@example.com"
		email_b = f"portal.b.{frappe.generate_hash(length=4)}@example.com"
		cust_a, _contact_a = _create_customer_with_contact(email_a)
		cust_b, _contact_b = _create_customer_with_contact(email_b)
		user_a = _create_website_user(email_a)
		user_b = _create_website_user(email_b)
		veh_a = _create_vehicle(cust_a.name)
		veh_b = _create_vehicle(cust_b.name)
		rec_a = _create_reception(cust_a.name, veh_a.name, self.employee.name)
		rec_b = _create_reception(cust_b.name, veh_b.name, self.employee.name)
		_create_service_order(cust_a.name, veh_a.name, rec_a)
		so_b = _create_service_order(cust_b.name, veh_b.name, rec_b)
		_create_quotation(cust_a.name)
		quot_b = _create_quotation(cust_b.name)

		from subamaz.api.portal import (
			get_my_vehicles,
			get_quotation,
			get_vehicle_detail,
		)

		# user A sees only own vehicle
		frappe.set_user(user_a)
		try:
			vehicles_a = get_my_vehicles()
			self.assertTrue(any(v["name"] == veh_a.name for v in vehicles_a))
			self.assertFalse(any(v["name"] == veh_b.name for v in vehicles_a))
			# direct vehicle detail of B should be denied
			self.assertRaises(frappe.PermissionError, get_vehicle_detail, veh_b.name)
			# quotation of A accessible, but no way to access raw B quotation via filter — get_quotation with B's doc should be denied
			self.assertRaises(frappe.PermissionError, get_quotation, quot_b.name)
			# ownership on service orders - get_service_order_progress should deny
			from subamaz.api.portal import get_service_order_progress

			self.assertRaises(frappe.PermissionError, get_service_order_progress, so_b.name)
		finally:
			frappe.set_user("Administrator")

		# user B cannot see A's data
		frappe.set_user(user_b)
		try:
			vehicles_b = get_my_vehicles()
			self.assertTrue(any(v["name"] == veh_b.name for v in vehicles_b))
			self.assertFalse(any(v["name"] == veh_a.name for v in vehicles_b))
			self.assertRaises(frappe.PermissionError, get_vehicle_detail, veh_a.name)
		finally:
			frappe.set_user("Administrator")

	def test_timeline_visibility(self):
		email = f"portal.tl.{frappe.generate_hash(length=4)}@example.com"
		cust, _contact = _create_customer_with_contact(email)
		user = _create_website_user(email)
		veh = _create_vehicle(cust.name)
		rec = _create_reception(cust.name, veh.name, self.employee.name)
		so = _create_service_order(cust.name, veh.name, rec)

		# append two timeline entries: one visible, one hidden
		doc = frappe.get_doc("Service Order", so.name)
		doc.append(
			"timeline",
			{
				"timestamp": frappe.utils.now_datetime(),
				"user": "Administrator",
				"event_type": "Status Change",
				"description": "Visible entry",
				"visible_to_customer": 1,
			},
		)
		doc.append(
			"timeline",
			{
				"timestamp": frappe.utils.now_datetime(),
				"user": "Administrator",
				"event_type": "Note",
				"description": "Hidden entry",
				"visible_to_customer": 0,
			},
		)
		doc.save(ignore_permissions=True)

		from subamaz.api.portal import get_customer_timeline

		frappe.set_user(user)
		try:
			entries = get_customer_timeline(service_order=so.name)
			descriptions = [e["description"] for e in entries]
			self.assertIn("Visible entry", descriptions)
			self.assertNotIn("Hidden entry", descriptions)
			for e in entries:
				self.assertEqual(e["visible_to_customer"], 1)
		finally:
			frappe.set_user("Administrator")

	def test_quotation_approve(self):
		email = f"portal.q.{frappe.generate_hash(length=4)}@example.com"
		cust, _contact = _create_customer_with_contact(email)
		user = _create_website_user(email)
		veh = _create_vehicle(cust.name)
		rec = _create_reception(cust.name, veh.name, self.employee.name)
		quot = _create_quotation(cust.name)
		quot2 = _create_quotation(cust.name)
		_create_service_order(cust.name, veh.name, rec, quotation=quot.name)

		from subamaz.api.portal import approve_quotation

		frappe.set_user(user)
		try:
			result = approve_quotation(quot.name, action="Approve")
			self.assertEqual(result["status"], "Approved")
			self.assertEqual(frappe.db.get_value("Quotation", quot.name, "status"), "Ordered")
			result2 = approve_quotation(quot2.name, action="Reject")
			self.assertEqual(result2["status"], "Rejected")
			self.assertEqual(frappe.db.get_value("Quotation", quot2.name, "status"), "Cancelled")
		finally:
			frappe.set_user("Administrator")

	def test_no_customer_user_error(self):
		email = f"portal.nocust.{frappe.generate_hash(length=4)}@example.com"
		# create Website User with no Contact/Customer linkage
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "NoCust",
					"send_welcome_email": 0,
					"user_type": "Website User",
				}
			).insert(ignore_permissions=True)

		from subamaz.api.portal import get_my_vehicles

		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.ValidationError) as cm:
				get_my_vehicles()
			self.assertIn("No linked Customer", str(cm.exception))
			# ensure no traceback leakage - exception message is clean
			self.assertNotIn("Traceback", str(cm.exception))
		finally:
			frappe.set_user("Administrator")

	def test_progress_aggregation(self):
		email = f"portal.prog.{frappe.generate_hash(length=4)}@example.com"
		cust, _contact = _create_customer_with_contact(email)
		user = _create_website_user(email)
		veh = _create_vehicle(cust.name)
		rec = _create_reception(cust.name, veh.name, self.employee.name)
		so = _create_service_order(cust.name, veh.name, rec)

		# create a job card that would leak raw name if exposed — rollup will recompute completion
		dept = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"DeptProg {frappe.generate_hash(length=4)}", "default_hourly_rate": 4000}
		).insert(ignore_permissions=True)
		emp2 = _create_employee()
		jc = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": so.name,
				"department": dept.name,
				"lead_technician": emp2.name,
				"status": "Working",
				"completion_percent": 50,
			}
		).insert(ignore_permissions=True)
		# set aggregated fields after job card so rollup does not overwrite
		frappe.db.set_value("Service Order", so.name, "completion_percent", 42)
		frappe.db.set_value("Service Order", so.name, "estimated_total", 50000)
		frappe.db.set_value("Service Order", so.name, "actual_total", 12000)

		from subamaz.api.portal import get_service_order_progress

		frappe.set_user(user)
		try:
			progress = get_service_order_progress(so.name)
			self.assertEqual(progress["completion_percent"], 42)
			self.assertIn("status", progress)
			self.assertIn("estimated_total", progress)
			self.assertNotIn("job_card", str(progress).lower())
			# ensure raw job card name not leaked
			self.assertNotIn(jc.name, str(progress))
			# internal fields not exposed
			self.assertNotIn("internal_notes", progress)
		finally:
			frappe.set_user("Administrator")
