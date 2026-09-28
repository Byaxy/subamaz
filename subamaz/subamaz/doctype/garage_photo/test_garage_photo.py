# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase


class TestGaragePhoto(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Photo Cust {frappe.generate_hash(length=4)}"}
		).insert()

	def _vehicle_with_photo(self, include_file=True):
		row = {"photo_type": "Front", "taken_on": frappe.utils.now_datetime()}
		if include_file:
			row["photo"] = "/files/test-vehicle.jpg"
		return frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"PH-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"photos": [row],
			}
		)

	def test_child_row_requires_photo(self):
		doc = self._vehicle_with_photo(include_file=False)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_child_row_with_photo_saves(self):
		doc = self._vehicle_with_photo().insert()
		reloaded = frappe.get_doc("Garage Vehicle", doc.name)
		self.assertEqual(reloaded.photos[0].photo, "/files/test-vehicle.jpg")
		self.assertEqual(reloaded.photos[0].photo_type, "Front")

	def test_photo_type_options(self):
		options = frappe.get_meta("Garage Photo").get_field("photo_type").options.split("\n")
		expected = [
			"Front",
			"Rear",
			"Left Side",
			"Right Side",
			"Interior",
			"Dashboard",
			"Engine Bay",
			"Damage Close-up",
			"Before",
			"During",
			"After",
		]
		self.assertEqual(options, expected)
