# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase


class TestVehicleModel(SubamazTestCase):
	def setUp(self):
		super().setUp()
		suffix = frappe.generate_hash(length=4)
		self.make = frappe.get_doc({"doctype": "Vehicle Make", "make_name": f"TestMake {suffix}"}).insert().name
		self.other_make = frappe.get_doc({"doctype": "Vehicle Make", "make_name": f"OtherMake {suffix}"}).insert().name

	def _make_model(self, model_name="TestModel", make=None):
		return frappe.get_doc(
			{"doctype": "Vehicle Model", "model_name": model_name, "make": make or self.make}
		)

	def test_create_model(self):
		doc = self._make_model().insert()
		self.assertEqual(doc.name, "TestModel")

	def test_duplicate_model_per_make_blocked(self):
		self._make_model().insert()
		duplicate = self._make_model()
		self.assertRaises(frappe.ValidationError, duplicate.insert)

	def test_same_model_different_make_blocked(self):
		# Names come from model_name, so a model name can only exist once globally.
		self._make_model().insert()
		duplicate = self._make_model(make=self.other_make)
		self.assertRaises(frappe.DuplicateEntryError, duplicate.insert)

	def test_make_required(self):
		doc = frappe.get_doc({"doctype": "Vehicle Model", "model_name": "NoMake"})
		self.assertRaises(frappe.MandatoryError, doc.insert)
