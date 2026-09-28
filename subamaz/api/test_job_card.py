# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestJobCardAPI(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"JCAPI Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"JCA-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "JCAPI",
				"last_name": f"Tech {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		self.department = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"DeptAPI {frappe.generate_hash(length=4)}", "default_hourly_rate": 4000}
		).insert()
		self.reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "API test",
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
		self.job_card = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
				"status": "Draft",
			}
		).insert()

	def test_start_job_transitions_to_working(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			from subamaz.api.job_card import start_job

			self.job_card.status = "Assigned"
			self.job_card.save()
			self.job_card.status = "Accepted"
			self.job_card.save()
			result = start_job(self.job_card.name)
			self.assertEqual(result["status"], "Working")
			doc = frappe.get_doc("Garage Job Card", self.job_card.name)
			self.assertEqual(doc.status, "Working")
			self.assertTrue(len(doc.time_logs) >= 1)
		finally:
			frappe.set_user("Administrator")

	def test_pause_job_closes_time_log(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			from subamaz.api.job_card import pause_job, start_job

			self.job_card.status = "Assigned"
			self.job_card.save()
			self.job_card.status = "Accepted"
			self.job_card.save()
			start_job(self.job_card.name)
			result = pause_job(self.job_card.name)
			self.assertEqual(result["status"], "Paused")
			doc = frappe.get_doc("Garage Job Card", self.job_card.name)
			self.assertEqual(doc.status, "Paused")
			# time log should have finished_at set
			self.assertTrue(doc.time_logs[0].finished_at)
		finally:
			frappe.set_user("Administrator")

	def test_complete_job_transitions_to_ready_qa_and_submits(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			from subamaz.api.job_card import complete_job, start_job

			self.job_card.status = "Assigned"
			self.job_card.save()
			self.job_card.status = "Accepted"
			self.job_card.save()
			start_job(self.job_card.name)
			result = complete_job(self.job_card.name)
			self.assertEqual(result["status"], "Ready QA")
			doc = frappe.get_doc("Garage Job Card", self.job_card.name)
			self.assertEqual(doc.status, "Ready QA")
			self.assertEqual(doc.docstatus, 1)
		finally:
			frappe.set_user("Administrator")

	def test_consume_part_creates_stock_entry(self):
		# Ensure item and warehouse with stock
		item_code = self._ensure_stock_item()
		warehouse = self._ensure_warehouse()
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			from subamaz.api.job_card import consume_part

			result = consume_part(self.job_card.name, item_code, 1, warehouse)
			self.assertTrue(result["stock_entry"])
			se = frappe.get_doc("Stock Entry", result["stock_entry"])
			self.assertEqual(se.docstatus, 1)
			self.assertEqual(se.garage_job_card, self.job_card.name)
			jc = frappe.get_doc("Garage Job Card", self.job_card.name)
			self.assertTrue(any(r.stock_entry == se.name for r in jc.consumed_parts))
		finally:
			frappe.set_user("Administrator")

	def test_start_job_denied_for_reception(self):
		user = self._create_user("Garage Reception")
		frappe.set_user(user)
		try:
			from subamaz.api.job_card import start_job

			self.assertRaises(frappe.PermissionError, start_job, self.job_card.name)
		finally:
			frappe.set_user("Administrator")

	def _ensure_stock_item(self):
		item_code = frappe.db.get_value(
			"Item", {"is_stock_item": 1, "is_fixed_asset": 0, "has_serial_no": 0, "has_batch_no": 0}, "item_code"
		)
		if not item_code:
			item = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": f"StockItem-{frappe.generate_hash(length=4)}",
					"item_name": "Stock Item",
					"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
					"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
					"is_stock_item": 1,
					"valuation_rate": 1000,
				}
			).insert()
			item_code = item.name
		warehouse = self._ensure_warehouse()
		warehouse_company = frappe.db.get_value("Warehouse", warehouse, "company")
		company = warehouse_company or frappe.db.get_value("Company", {}, "name")
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"purpose": "Material Receipt",
				"company": company,
				"items": [{"item_code": item_code, "qty": 10, "t_warehouse": warehouse, "basic_rate": 1000}],
			}
		).insert()
		se.submit()
		return item_code

	def _ensure_warehouse(self):
		company = frappe.db.get_value("Company", {}, "name")
		wh = frappe.db.get_value("Warehouse", {"company": company}, "name")
		if wh:
			return wh
		# create for this company to avoid cross-company mismatch
		wh_doc = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": f"WH-{frappe.generate_hash(length=4)}", "company": company}).insert()
		return wh_doc.name

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.jcapi@example.com"
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
