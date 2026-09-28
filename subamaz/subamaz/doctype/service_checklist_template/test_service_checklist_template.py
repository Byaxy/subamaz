# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase


class TestServiceChecklistTemplate(SubamazTestCase):
	def test_items_round_trip(self):
		doc = frappe.get_doc(
			{
				"doctype": "Service Checklist Template",
				"template_name": f"Oil Change {frappe.generate_hash(length=4)}",
				"applies_to": "Repair",
				"items": [
					{"item_description": "Drain old oil", "default_expected_result": "Oil drained"},
					{
						"item_description": "Replace filter",
						"default_expected_result": "New filter fitted",
					},
				],
			}
		).insert()
		reloaded = frappe.get_doc("Service Checklist Template", doc.name)
		self.assertEqual(len(reloaded.items), 2)
		self.assertEqual(reloaded.items[0].item_description, "Drain old oil")

	def test_applies_to_validates_against_options(self):
		doc = frappe.get_doc(
			{
				"doctype": "Service Checklist Template",
				"template_name": f"Bogus {frappe.generate_hash(length=4)}",
				"applies_to": "Bogus",
				"items": [{"item_description": "Check"}],
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_applies_to_options(self):
		options = frappe.get_meta("Service Checklist Template").get_field("applies_to").options
		self.assertEqual(options.split("\n"), ["Inspection", "Repair", "Delivery", "QA"])
