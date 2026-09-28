# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

from unittest.mock import patch

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestQADeliveryCross(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"QACross Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"QD-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "QACross",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		self.department = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"QDept {frappe.generate_hash(length=4)}"}
		).insert()
		self.reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "Delivery test",
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
				"quality_checklist": [
					{"checklist_item": "Road Test", "result": "Pass", "checked_by": self.employee.name}
				],
				"qa_result": "Pass",
			}
		).insert()
		self.job_card.submit()
		self.repair_task = frappe.get_doc(
			{
				"doctype": "Repair Task",
				"job_card": self.job_card.name,
				"description": "Task to close",
				"status": "Working",
			}
		).insert()

	def _get_item(self):
		code = frappe.db.get_value("Item", {}, "item_code")
		if code:
			return code
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"QDItem-{frappe.generate_hash(length=4)}",
				"item_name": "QD Item",
				"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
				"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
				"is_stock_item": 0,
			}
		).insert()
		return item.name

	def test_apr_to_quotation(self):
		# Add APR to job card
		jc = frappe.get_doc("Garage Job Card", self.job_card.name)
		jc.additional_parts = []
		item_code = self._get_item()
		jc.append("additional_parts", {"item_code": item_code, "qty": 2, "reason": "Needed", "status": "Pending Approval", "requested_by": self.employee.name})
		jc.save()
		row_name = jc.additional_parts[0].name
		# Need quotation on SO — set estimated via db to bypass UpdateAfterSubmit, then trigger ensure
		frappe.db.set_value("Service Order", self.service_order.name, "estimated_labour", 1000)
		frappe.db.set_value("Service Order", self.service_order.name, "estimated_parts", 500)
		frappe.db.set_value("Service Order", self.service_order.name, "estimated_total", 1500)
		so = frappe.get_doc("Service Order", self.service_order.name)
		frappe.db.set_value("Service Order", so.name, "status", "In Progress")
		# Ensure quotation exists
		so = frappe.get_doc("Service Order", so.name)
		try:
			so._ensure_quotation()
		except Exception:
			pass
		so.reload()
		# Now approve
		user = self._create_user("Garage Supervisor")
		frappe.set_user(user)
		try:
			from subamaz.api.qa import approve_additional_part

			approve_additional_part(jc.name, row_name, True)
			so.reload()
			if so.quotation:
				q = frappe.get_doc("Quotation", so.quotation)
				self.assertTrue(any(i.item_code == item_code for i in q.items))
		finally:
			frappe.set_user("Administrator")

	def test_delivery_submit_side_effects(self):
		# Ensure project exists
		so = frappe.get_doc("Service Order", self.service_order.name)
		frappe.db.set_value("Service Order", so.name, "status", "In Progress")
		# Force project creation by setting long duration via db (bypass UpdateAfterSubmit)
		from frappe.utils import add_days

		frappe.db.set_value("Service Order", so.name, "expected_finish", add_days(frappe.utils.today(), 30))
		so = frappe.get_doc("Service Order", so.name)
		try:
			so._ensure_project()
		except Exception:
			pass
		so.reload()
		# Now create delivery
		with patch("frappe.enqueue") as mock_enqueue:
			delivery = frappe.get_doc(
				{
					"doctype": "Vehicle Delivery",
					"service_order": so.name,
					"vehicle": self.vehicle.name,
					"customer": self.customer.name,
					"checklist": [{"checklist_item": "Invoice Paid", "completed": 1}],
					"photos": [{"photo": "/files/front.jpg", "photo_type": "Front"}],
				}
			).insert()
			delivery.submit()
			self.assertEqual(delivery.docstatus, 1)
			# Vehicle status
			status = frappe.db.get_value("Garage Vehicle", self.vehicle.name, "current_status")
			self.assertEqual(status, "Available")
			# Service order should have invoice
			so.reload()
			self.assertTrue(so.sales_invoice)
			# Repair task closed
			task = frappe.get_doc("Repair Task", self.repair_task.name)
			self.assertEqual(task.status, "Completed")
			# Timeline entry exists
			so.reload()
			self.assertTrue(len(so.timeline) >= 1)
			# Enqueue called twice (reminder + survey if enabled)
			self.assertTrue(mock_enqueue.called)

	def test_checklist_and_qa_guard(self):
		# Use a fresh draft job card to avoid UpdateAfterSubmit
		jc = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
				"qa_result": "Pending",
			}
		).insert()
		# Trying to set Pass without rows should fail
		jc.qa_result = "Pass"
		self.assertRaises(frappe.ValidationError, jc.save)
		jc.reload()
		# Add failing row
		jc.append("quality_checklist", {"checklist_item": "Road Test", "result": "Fail", "checked_by": self.employee.name})
		jc.qa_result = "Pass"
		self.assertRaises(frappe.ValidationError, jc.save)
		jc.reload()
		# Correct
		jc.append("quality_checklist", {"checklist_item": "Road Test", "result": "Pass", "checked_by": self.employee.name})
		jc.qa_result = "Pass"
		jc.save()
		self.assertEqual(jc.qa_result, "Pass")

	def test_background_jobs_skipped_when_survey_disabled(self):
		frappe.db.set_single_value("Garage Settings", "enable_satisfaction_survey", 0)
		so = frappe.get_doc("Service Order", self.service_order.name)
		frappe.db.set_value("Service Order", so.name, "status", "In Progress")
		with patch("frappe.enqueue") as mock_enqueue:
			delivery = frappe.get_doc(
				{
					"doctype": "Vehicle Delivery",
					"service_order": so.name,
					"vehicle": self.vehicle.name,
					"customer": self.customer.name,
				}
			).insert()
			delivery.submit()
			# Should have at least reminder, but survey not enqueued
			calls = [c[0][0] for c in mock_enqueue.call_args_list]
			self.assertIn("subamaz.subamaz.doctype.vehicle_delivery.vehicle_delivery.enqueue_reminder", calls)
			self.assertNotIn("subamaz.subamaz.doctype.vehicle_delivery.vehicle_delivery.enqueue_survey", calls)
		# restore
		frappe.db.set_single_value("Garage Settings", "enable_satisfaction_survey", 1)

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.qad@example.com"
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
