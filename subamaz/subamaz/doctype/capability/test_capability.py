# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestCapability(IntegrationTestCase):
	def test_capability_create_and_unique(self):
		key = f"module:test_{frappe.generate_hash(length=4)}"
		frappe.get_doc(
			{
				"doctype": "Capability",
				"capability_key": key,
				"label": "Test Module",
				"capability_type": "Module",
				"module_group": "SERVICE",
				"default_enabled": 1,
			}
		).insert()
		self.assertTrue(frappe.db.exists("Capability", key))
		# duplicate should throw (DB level DuplicateEntryError)
		dup = frappe.get_doc(
			{
				"doctype": "Capability",
				"capability_key": key,
				"label": "Duplicate",
				"capability_type": "Module",
				"module_group": "SERVICE",
			}
		)
		self.assertRaises((frappe.exceptions.ValidationError, frappe.exceptions.DuplicateEntryError), dup.insert)

	def test_capability_fields_roundtrip(self):
		key = f"action:test_{frappe.generate_hash(length=4)}"
		frappe.get_doc(
			{
				"doctype": "Capability",
				"capability_key": key,
				"label": "Test Action",
				"capability_type": "Action",
				"module_group": "SERVICE",
				"default_enabled": 0,
			}
		).insert()
		reloaded = frappe.get_doc("Capability", key)
		self.assertEqual(reloaded.capability_type, "Action")
		self.assertEqual(reloaded.default_enabled, 0)

	def test_capability_permissions(self):
		meta = frappe.get_meta("Capability")
		roles = {p.role for p in meta.permissions}
		self.assertIn("System Manager", roles)
		self.assertIn("Garage Manager", roles)
