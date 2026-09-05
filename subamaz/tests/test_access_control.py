# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

from subamaz.api.access_control import has_capability


class TestAccessControlCross(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		from subamaz.api.access_control import _ensure_capabilities

		_ensure_capabilities()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"ACCross Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"AC-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "ACCross",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		self.department = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"ACDept {frappe.generate_hash(length=4)}"}
		).insert()
		self.reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "AC test",
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
				"item_code": f"ACItem-{frappe.generate_hash(length=4)}",
				"item_name": "AC Item",
				"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
				"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
				"is_stock_item": 0,
			}
		).insert()
		return item.name

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.accross_{frappe.generate_hash(length=4)}@example.com"
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

	def _set_role_capability(self, role, capability, enabled):
		name = frappe.db.get_value("Role Capability", {"role": role, "capability": capability}, "name")
		if name:
			frappe.db.set_value("Role Capability", name, "enabled", 1 if enabled else 0)
		else:
			frappe.get_doc(
				{"doctype": "Role Capability", "role": role, "capability": capability, "enabled": 1 if enabled else 0}
			).insert(ignore_permissions=True)

	def test_ceiling_enforcement_stray_row_ignored(self):
		# Technician has no action:approve_additional_part in ceiling — stray enabled=1 must not grant
		self._set_role_capability("Garage Technician", "action:approve_additional_part", 1)
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			self.assertFalse(has_capability(user, "action:approve_additional_part"))
		finally:
			frappe.set_user("Administrator")

	def test_toggle_effect_flips_has_capability(self):
		role = "Garage Service Advisor"
		user = self._create_user(role)
		self._set_role_capability(role, "action:approve_additional_part", 1)
		frappe.set_user(user)
		try:
			self.assertTrue(has_capability(user, "action:approve_additional_part"))
			self._set_role_capability(role, "action:approve_additional_part", 0)
			self.assertFalse(has_capability(user, "action:approve_additional_part"))
		finally:
			frappe.set_user("Administrator")

	def test_retrofit_approve_denied_when_capability_disabled(self):
		role = "Garage Service Advisor"
		user = self._create_user(role)
		self._set_role_capability(role, "action:approve_additional_part", 0)
		frappe.set_user(user)
		try:
			from subamaz.api.qa import approve_additional_part

			row_name = self.job_card.additional_parts[0].name
			self.assertRaises(frappe.PermissionError, approve_additional_part, self.job_card.name, row_name, True)
		finally:
			frappe.set_user("Administrator")

	def test_retrofit_approve_allowed_when_enabled(self):
		role = "Garage Service Advisor"
		user = self._create_user(role)
		self._set_role_capability(role, "action:approve_additional_part", 1)
		frappe.set_user(user)
		try:
			from subamaz.api.qa import approve_additional_part

			row_name = self.job_card.additional_parts[0].name
			result = approve_additional_part(self.job_card.name, row_name, True)
			self.assertEqual(result["status"], "Approved")
		finally:
			frappe.set_user("Administrator")

	def test_get_my_capabilities_keys(self):
		user = self._create_user("Garage Reception")
		frappe.set_user(user)
		try:
			from subamaz.api.access_control import get_my_capabilities

			caps = get_my_capabilities()
			# all DEFAULT keys present
			from subamaz.api.access_control import DEFAULT_CAPABILITIES

			for cap in DEFAULT_CAPABILITIES:
				self.assertIn(cap["capability_key"], caps)
		finally:
			frappe.set_user("Administrator")

	def test_uniqueness_duplicate_role_capability_throws(self):
		cap = f"module:test_uniq_{frappe.generate_hash(length=4)}"
		# ensure capability exists (unique key not in seed)
		if not frappe.db.exists("Capability", cap):
			frappe.get_doc(
				{
					"doctype": "Capability",
					"capability_key": cap,
					"label": "Test Unique",
					"capability_type": "Module",
					"module_group": "SERVICE",
				}
			).insert()
		frappe.get_doc({"doctype": "Role Capability", "role": "Garage Inspector", "capability": cap, "enabled": 1}).insert()
		dup = frappe.get_doc({"doctype": "Role Capability", "role": "Garage Inspector", "capability": cap, "enabled": 0})
		self.assertRaises(frappe.ValidationError, dup.insert)
