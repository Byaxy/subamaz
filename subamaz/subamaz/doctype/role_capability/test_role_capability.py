# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestRoleCapability(SubamazTestCase):
	def setUp(self):
		super().setUp()
		# ensure capability exists
		self.cap_key = f"module:test_rc_{frappe.generate_hash(length=4)}"
		if not frappe.db.exists("Capability", self.cap_key):
			frappe.get_doc(
				{
					"doctype": "Capability",
					"capability_key": self.cap_key,
					"label": "RC Test",
					"capability_type": "Module",
					"module_group": "SERVICE",
					"default_enabled": 1,
				}
			).insert()

	def test_role_capability_create(self):
		doc = frappe.get_doc(
			{"doctype": "Role Capability", "role": "Garage Technician", "capability": self.cap_key, "enabled": 1}
		).insert()
		self.assertTrue(doc.name)
		reloaded = frappe.get_doc("Role Capability", doc.name)
		self.assertEqual(reloaded.enabled, 1)

	def test_role_capability_uniqueness(self):
		frappe.get_doc(
			{"doctype": "Role Capability", "role": "Garage Reception", "capability": self.cap_key, "enabled": 1}
		).insert()
		dup = frappe.get_doc(
			{"doctype": "Role Capability", "role": "Garage Reception", "capability": self.cap_key, "enabled": 0}
		)
		self.assertRaises(frappe.ValidationError, dup.insert)

	def test_permissions(self):
		meta = frappe.get_meta("Role Capability")
		roles = {p.role for p in meta.permissions}
		self.assertIn("System Manager", roles)
		self.assertIn("Garage Manager", roles)
