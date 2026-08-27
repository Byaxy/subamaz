# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestQaAPI(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"QA Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"QA-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "QA",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		self.department = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"QADept {frappe.generate_hash(length=4)}"}
		).insert()
		self.reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "QA test",
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
				"additional_parts": [
					{"item_code": self._get_item(), "qty": 1, "reason": "Leak", "status": "Pending Approval", "requested_by": self.employee.name}
				],
			}
		).insert()

	def _get_item(self):
		code = frappe.db.get_value("Item", {}, "item_code")
		if code:
			return code
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"QAItem-{frappe.generate_hash(length=4)}",
				"item_name": "QA Item",
				"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
				"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
				"is_stock_item": 0,
			}
		).insert()
		return item.name

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.qa@example.com"
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

	def test_approve_as_allowed_role(self):
		user = self._create_user("Garage Service Advisor")
		frappe.set_user(user)
		try:
			from subamaz.api.qa import approve_additional_part

			row_name = self.job_card.additional_parts[0].name
			result = approve_additional_part(self.job_card.name, row_name, approve=True)
			self.assertEqual(result["status"], "Approved")
			doc = frappe.get_doc("Garage Job Card", self.job_card.name)
			self.assertEqual(doc.additional_parts[0].status, "Approved")
			self.assertTrue(doc.additional_parts[0].approved_by)
		finally:
			frappe.set_user("Administrator")

	def test_reject_path(self):
		user = self._create_user("Garage Supervisor")
		frappe.set_user(user)
		try:
			from subamaz.api.qa import approve_additional_part

			row_name = self.job_card.additional_parts[0].name
			result = approve_additional_part(self.job_card.name, row_name, approve=False)
			self.assertEqual(result["status"], "Rejected")
		finally:
			frappe.set_user("Administrator")

	def test_denied_for_technician(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			from subamaz.api.qa import approve_additional_part

			row_name = self.job_card.additional_parts[0].name
			self.assertRaises(frappe.PermissionError, approve_additional_part, self.job_card.name, row_name, True)
		finally:
			frappe.set_user("Administrator")
