# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase


class TestGarageDepartment(SubamazTestCase):
	def test_rate_persists_and_is_active_defaults_on(self):
		doc = frappe.get_doc(
			{
				"doctype": "Garage Department",
				"department_name": f"Engine {frappe.generate_hash(length=4)}",
				"default_hourly_rate": 150000,
			}
		).insert()
		reloaded = frappe.get_doc("Garage Department", doc.name)
		self.assertEqual(reloaded.default_hourly_rate, 150000)
		self.assertEqual(reloaded.is_active, 1)

	def test_is_active_can_be_turned_off(self):
		doc = frappe.get_doc(
			{
				"doctype": "Garage Department",
				"department_name": f"Body {frappe.generate_hash(length=4)}",
				"is_active": 0,
			}
		).insert()
		reloaded = frappe.get_doc("Garage Department", doc.name)
		self.assertEqual(reloaded.is_active, 0)
