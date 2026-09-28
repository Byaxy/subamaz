# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

from subamaz.api.access_control import (
	DEFAULT_CAPABILITIES,
	ROLE_CEILING,
	get_access_control_grid,
	get_my_capabilities,
	has_capability,
	save_access_control_grid,
)


def _ensure_caps():
	from subamaz.api.access_control import _ensure_capabilities

	_ensure_capabilities()


class TestAccessControlAPI(SubamazTestCase):
	def setUp(self):
		super().setUp()
		_ensure_caps()

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.ac_{frappe.generate_hash(length=4)}@example.com"
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

	def test_has_capability_toggle_effect(self):
		user = self._create_user("Garage Service Advisor")
		# ensure enabled (default)
		self._set_role_capability("Garage Service Advisor", "action:approve_additional_part", 1)
		frappe.set_user(user)
		try:
			self.assertTrue(has_capability(user, "action:approve_additional_part"))
			self._set_role_capability("Garage Service Advisor", "action:approve_additional_part", 0)
			self.assertFalse(has_capability(user, "action:approve_additional_part"))
			self._set_role_capability("Garage Service Advisor", "action:approve_additional_part", 1)
			self.assertTrue(has_capability(user, "action:approve_additional_part"))
		finally:
			frappe.set_user("Administrator")

	def test_has_capability_returns_false_for_outside_ceiling(self):
		# Technician has no action:approve_additional_part in ceiling
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			self.assertFalse(has_capability(user, "action:approve_additional_part"))
		finally:
			frappe.set_user("Administrator")

	def test_get_my_capabilities_consistent_with_ceiling(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			caps = get_my_capabilities()
			# Technician should have service, customers_vehicles, parts_stock, insights
			self.assertTrue(caps.get("module:service"))
			self.assertTrue(caps.get("module:customers_vehicles"))
			self.assertTrue(caps.get("module:parts_stock"))
			self.assertTrue(caps.get("module:insights"))
			self.assertFalse(caps.get("module:procurement"))
			self.assertFalse(caps.get("module:staff"))
			self.assertFalse(caps.get("action:approve_additional_part"))
		finally:
			frappe.set_user("Administrator")

	def test_get_access_control_grid_marks_ceiling(self):
		manager = self._create_user("Garage Manager")
		frappe.set_user(manager)
		try:
			grid = get_access_control_grid()
			self.assertIn("roles", grid)
			self.assertIn("capabilities", grid)
			self.assertIn("grid", grid)
			# find a cell known to be outside ceiling: Technician + STAFF
			tech_staff = [c for c in grid["grid"] if c["role"] == "Garage Technician" and c["capability"] == "module:staff"]
			self.assertTrue(tech_staff)
			self.assertEqual(tech_staff[0]["in_ceiling"], 0)
			self.assertEqual(tech_staff[0]["available"], 0)
			# inside ceiling: Technician service should be in_ceiling 1
			tech_service = [c for c in grid["grid"] if c["role"] == "Garage Technician" and c["capability"] == "module:service"]
			self.assertEqual(tech_service[0]["in_ceiling"], 1)
			# Manager should have everything in ceiling via "*"
			mgr_any = [c for c in grid["grid"] if c["role"] == "Garage Manager"]
			for cell in mgr_any:
				self.assertEqual(cell["in_ceiling"], 1, f"Manager should have {cell['capability']} in ceiling")
		finally:
			frappe.set_user("Administrator")

	def test_get_access_control_grid_manager_only(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			self.assertRaises(frappe.PermissionError, get_access_control_grid)
		finally:
			frappe.set_user("Administrator")

	def test_save_access_control_grid_upserts_and_refuses_outside_ceiling(self):
		manager = self._create_user("Garage Manager")
		frappe.set_user(manager)
		try:
			# valid change: toggle Reception petty cash
			self._set_role_capability("Garage Reception", "action:record_petty_cash", 1)
			result = save_access_control_grid(
				[{"role": "Garage Reception", "capability": "action:record_petty_cash", "enabled": 0}]
			)
			self.assertTrue(result["changed"])
			# verify persisted
			enabled = frappe.db.get_value("Role Capability", {"role": "Garage Reception", "capability": "action:record_petty_cash"}, "enabled")
			self.assertEqual(enabled, 0)
			# outside ceiling: Technician staff should throw
			self.assertRaises(
				frappe.ValidationError,
				save_access_control_grid,
				[{"role": "Garage Technician", "capability": "module:staff", "enabled": 1}],
			)
		finally:
			frappe.set_user("Administrator")

	def test_save_access_control_grid_manager_only(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		try:
			self.assertRaises(
				frappe.PermissionError,
				save_access_control_grid,
				[{"role": "Garage Reception", "capability": "module:service", "enabled": 1}],
			)
		finally:
			frappe.set_user("Administrator")
