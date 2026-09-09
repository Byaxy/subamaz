# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer", "Employee"]


class TestVehicleInspection(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Insp Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = self._make_vehicle()
		self.inspector = self._make_employee()

	def _make_employee(self):
		return frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Inspector",
				"last_name": f"Test {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()

	def _make_vehicle(self):
		suffix = frappe.generate_hash(length=5)
		return frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"VI-{suffix}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"current_mileage": 10000,
			}
		).insert()

	def _make_inspection(self, **overrides):
		doc = frappe.get_doc(
			{
				"doctype": "Vehicle Inspection",
				"vehicle": self.vehicle.name,
				"customer": self.customer.name,
				"inspector": self.inspector.name,
				"inspection_type": "Routine",
				"mileage": 10000,
				"checklist": [
					{
						"section": "Engine",
						"checklist_item": "Oil Leak",
						"result": "Pass",
					},
					{
						"section": "Electrical",
						"checklist_item": "Battery",
						"result": "Advisory",
						"notes": "Weak",
					},
				],
				"inspection_result": "Good",
				"recommendation": "Safe to Drive",
			}
		)
		doc.update(overrides)
		return doc

	def test_naming_series(self):
		doc = self._make_inspection().insert()
		self.assertRegex(doc.name, r"^INSP-\d{4}-\d{5}$")

	def test_customer_autofill(self):
		doc = self._make_inspection(customer=None)
		# bypass setting customer, let validate fill it
		doc.customer = None
		doc.insert()
		self.assertEqual(doc.customer, self.customer.name)

	def test_create_and_submit(self):
		doc = self._make_inspection().insert()
		doc.submit()
		self.assertEqual(doc.docstatus, 1)

	def test_checklist_roundtrip(self):
		doc = self._make_inspection().insert()
		doc.submit()
		reloaded = frappe.get_doc("Vehicle Inspection", doc.name)
		self.assertEqual(len(reloaded.checklist), 2)
		self.assertEqual(reloaded.checklist[0].section, "Engine")

	def test_inspection_result_select_options(self):
		meta = frappe.get_meta("Vehicle Inspection")
		options = meta.get_field("inspection_result").options.split("\n")
		for val in ("Excellent", "Good", "Fair", "Poor", "Critical"):
			self.assertIn(val, options)
		for val in ("Pass", "Fail"):
			self.assertNotIn(val, options)

	def test_recommendation_select_options(self):
		meta = frappe.get_meta("Vehicle Inspection")
		options = meta.get_field("recommendation").options.split("\n")
		for val in ("Safe to Drive", "Needs Repairs", "Unsafe", "Further Diagnosis"):
			self.assertIn(val, options)
		for val in ("Service",):
			self.assertNotIn(val, options)

	def test_search_fields(self):
		search_fields = [
			f.strip() for f in (frappe.get_meta("Vehicle Inspection").search_fields or "").split(",")
		]
		for field in ("vehicle", "customer", "inspector"):
			self.assertIn(field, search_fields)

	def test_checklist_section_options(self):
		meta = frappe.get_meta("Inspection Checklist Item")
		options = meta.get_field("section").options.split("\n")
		for val in ("Engine", "Transmission", "Suspension", "Electrical", "Interior", "Exterior"):
			self.assertIn(val, options)

	def test_checklist_result_options(self):
		meta = frappe.get_meta("Inspection Checklist Item")
		options = meta.get_field("result").options.split("\n")
		for val in ("Pass", "Fail", "Advisory", "Not Checked"):
			self.assertIn(val, options)
