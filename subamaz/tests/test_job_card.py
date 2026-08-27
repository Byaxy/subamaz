# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestJobCardCross(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"JCCross Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"JCC-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "JCCross",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		self.department = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"DeptCross {frappe.generate_hash(length=4)}", "default_hourly_rate": 6000}
		).insert()
		self.reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "Cross",
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

	def test_so_rollup_updates_on_job_card_save(self):
		jc = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
				"status": "Draft",
				"estimated_cost": 5000,
			}
		).insert()
		jc.append("time_logs", {"technician": self.employee.name, "hours": 2, "hourly_rate": 6000})
		jc.save()
		so = frappe.get_doc("Service Order", self.service_order.name)
		# recompute_rollup should have been triggered via on_update
		self.assertGreaterEqual(so.estimated_labour, 5000)
		self.assertGreaterEqual(so.actual_labour, 0)

	def test_sibling_completion_advances_so(self):
		jc1 = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
				"status": "Working",
			}
		).insert()
		jc2 = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
				"status": "Working",
			}
		).insert()
		# Move SO to In Progress to test advance — bypass workflow validation
		frappe.db.set_value("Service Order", self.service_order.name, "status", "In Progress")
		so = frappe.get_doc("Service Order", self.service_order.name)
		# Complete first JC
		jc1.status = "Completed"
		jc1.submit()
		so.reload()
		# Not yet all done, status should remain In Progress
		self.assertEqual(so.status, "In Progress")
		# Complete second JC
		jc2.status = "Completed"
		jc2.submit()
		so.reload()
		self.assertEqual(so.status, "Quality Check")

	def test_repair_task_with_parent_and_assignment(self):
		jc = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
			}
		).insert()
		task = frappe.get_doc(
			{
				"doctype": "Repair Task",
				"job_card": jc.name,
				"description": "Parent task",
				"status": "Pending",
				"progress_percent": "0",
			}
		).insert()
		subtask = frappe.get_doc(
			{
				"doctype": "Repair Task",
				"job_card": jc.name,
				"parent_task": task.name,
				"description": "Subtask",
				"status": "Pending",
				"technician_assignments": [{"technician": self.employee.name, "role": "Primary", "hours": 2}],
			}
		).insert()
		self.assertEqual(subtask.parent_task, task.name)
		self.assertEqual(subtask.technician_assignments[0].technician, self.employee.name)

	def test_permissions_matrix_exists(self):
		for doctype in ("Garage Job Card", "Repair Task"):
			meta = frappe.get_meta(doctype)
			roles = {p.role for p in meta.permissions}
			self.assertIn("Garage Technician", roles)
			self.assertIn("Garage Manager", roles)
		jc_meta = frappe.get_meta("Garage Job Card")
		tech = next(p for p in jc_meta.permissions if p.role == "Garage Technician")
		self.assertTrue(tech.write)
		reception = next(p for p in jc_meta.permissions if p.role == "Garage Reception")
		self.assertFalse(reception.write)

	def test_vehicle_link_unchanged_after_job_card(self):
		jc = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": self.service_order.name,
				"department": self.department.name,
				"lead_technician": self.employee.name,
			}
		).insert()
		self.assertTrue(frappe.db.exists("Garage Job Card", jc.name))
		linked = frappe.db.get_value("Garage Vehicle", self.vehicle.name, "current_service_order")
		self.assertEqual(linked, self.service_order.name)
