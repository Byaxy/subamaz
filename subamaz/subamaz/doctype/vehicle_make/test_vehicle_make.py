# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase


class TestVehicleMake(SubamazTestCase):
	def test_create_make(self):
		name = f"TestMake {frappe.generate_hash(length=4)}"
		doc = frappe.get_doc({"doctype": "Vehicle Make", "make_name": name}).insert()
		self.assertEqual(doc.name, name)

	def test_duplicate_make_blocked(self):
		name = f"DupeMake {frappe.generate_hash(length=4)}"
		frappe.get_doc({"doctype": "Vehicle Make", "make_name": name}).insert()
		duplicate = frappe.get_doc({"doctype": "Vehicle Make", "make_name": name})
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)
