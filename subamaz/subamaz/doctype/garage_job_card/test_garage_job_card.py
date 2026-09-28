# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer", "Employee"]


class TestJobCard(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"JC Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"JC-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "JC",
				"last_name": f"Tech {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		self.department = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"Dept {frappe.generate_hash(length=4)}", "default_hourly_rate": 5000}
		).insert()
		self.reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "Test",
				"terms_accepted": 1,
				"photos": [
					{"photo": "/files/front.jpg", "photo_type": "Front"},
					{"photo": "/files/rear.jpg", "photo_type": "Rear"},
					{"photo": "/files/interior.jpg", "photo_type": "Interior"},
					{"photo": "/files/dashboard.jpg", "photo_type": "Dashboard"},
				],
			}
		).insert()
		self.reception.submit()
		self.service_order = frappe.get_doc(
			{
				"doctype": "Service Order",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"vehicle_reception": self.reception.name,
				"opening_date": frappe.utils.today(),
			}
		).insert()
		self.service_order.submit()

	def _make_job_card(self, **overrides):
		doc = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
				"status": "Draft",
				"estimated_hours": 5,
				"estimated_cost": 2000,
			}
		)
		doc.update(overrides)
		return doc

	def test_naming_series(self):
		doc = self._make_job_card().insert()
		self.assertRegex(doc.name, r"^GJC-\d{4}-\d{5}$")

	def test_actual_hours_and_cost_recomputed(self):
		doc = self._make_job_card().insert()
		doc.append("time_logs", {"technician": self.employee.name, "hours": 2, "hourly_rate": 5000})
		doc.append("time_logs", {"technician": self.employee.name, "hours": 3, "hourly_rate": 5000})
		doc.append("consumed_parts", {"item_code": self._get_item(), "qty": 2, "rate": 1000})
		doc.save()
		self.assertEqual(doc.actual_hours, 5)
		# 2*5000 +3*5000 =25000 + 2000 =27000
		self.assertEqual(doc.actual_cost, 27000)

	def test_valid_transitions(self):
		doc = self._make_job_card().insert()
		doc.status = "Assigned"
		doc.save()
		doc.status = "Accepted"
		doc.save()
		doc.status = "Working"
		doc.save()
		self.assertEqual(doc.status, "Working")

	def test_invalid_transition_throws(self):
		doc = self._make_job_card().insert()
		doc.status = "Completed"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_cancel_requires_manager(self):
		doc = self._make_job_card().insert()
		doc.status = "Assigned"
		doc.save()
		# try cancel as Technician (non-manager)
		tech_user = self._create_user("Garage Technician")
		frappe.set_user(tech_user)
		try:
			doc = frappe.get_doc("Garage Job Card", doc.name)
			doc.status = "Cancelled"
			self.assertRaises(frappe.PermissionError, doc.save)
		finally:
			frappe.set_user("Administrator")
		# Manager can cancel
		mgr = self._create_user("Garage Manager")
		frappe.set_user(mgr)
		try:
			doc = frappe.get_doc("Garage Job Card", doc.name)
			doc.status = "Cancelled"
			doc.save()
			self.assertEqual(doc.status, "Cancelled")
		finally:
			frappe.set_user("Administrator")

	def test_time_log_labour_cost_computed(self):
		doc = self._make_job_card().insert()
		doc.append("time_logs", {"technician": self.employee.name, "hours": 4, "hourly_rate": 2500})
		doc.save()
		self.assertEqual(doc.time_logs[0].labour_cost, 10000)

	def test_consumed_part_amount_computed(self):
		doc = self._make_job_card().insert()
		doc.append("consumed_parts", {"item_code": self._get_item(), "qty": 3, "rate": 1500})
		doc.save()
		self.assertEqual(doc.consumed_parts[0].amount, 4500)

	def test_search_fields(self):
		fields = [f.strip() for f in (frappe.get_meta("Garage Job Card").search_fields or "").split(",")]
		for f in ("service_order", "department", "lead_technician", "status"):
			self.assertIn(f, fields)

	def _get_item(self):
		item = frappe.db.get_value("Item", {}, "item_code")
		if item:
			return item
		# create fallback item
		it = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"TestItem-{frappe.generate_hash(length=4)}",
				"item_name": "Test Item",
				"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
				"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
				"is_stock_item": 1,
				"valuation_rate": 1000,
			}
		).insert()
		return it.name

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.jc@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role,
					"send_welcome_email": 0,
					"user_type": "System User",
					"roles": [{"role": role}],
				}
			)
			user.insert(ignore_permissions=True)
		return email
