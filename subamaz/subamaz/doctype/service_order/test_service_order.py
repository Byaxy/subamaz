# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer", "Employee"]


class TestServiceOrder(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"SO Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"SO-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"current_mileage": 10000,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "SO",
				"last_name": f"Advisor {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()
		self.reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "Noise",
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

	def _make_so(self, **overrides):
		doc = frappe.get_doc(
			{
				"doctype": "Service Order",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"vehicle_reception": self.reception.name,
				"opening_date": frappe.utils.today(),
				"priority": "Medium",
			}
		)
		doc.update(overrides)
		return doc

	def test_naming_series(self):
		doc = self._make_so().insert()
		self.assertRegex(doc.name, r"^SO-\d{4}-\d{5}$")

	def test_create_and_submit_sets_vehicle_link(self):
		doc = self._make_so().insert()
		doc.submit()
		self.assertEqual(doc.docstatus, 1)
		linked = frappe.db.get_value("Garage Vehicle", self.vehicle.name, "current_service_order")
		self.assertEqual(linked, doc.name)

	def test_search_fields(self):
		search_fields = [
			f.strip() for f in (frappe.get_meta("Service Order").search_fields or "").split(",")
		]
		for field in ("customer", "vehicle", "status"):
			self.assertIn(field, search_fields)

	def test_timeline_helper_appends(self):
		from subamaz.subamaz.doctype.service_order.service_order import add_timeline_entry

		doc = self._make_so().insert()
		add_timeline_entry(doc, "Test entry", "Note", visible=True)
		reloaded = frappe.get_doc("Service Order", doc.name)
		self.assertEqual(len(reloaded.timeline), 1)
		self.assertEqual(reloaded.timeline[0].description, "Test entry")
		self.assertEqual(reloaded.timeline[0].visible_to_customer, 1)

	def test_permissions_matrix(self):
		meta = frappe.get_meta("Service Order")
		roles = {p.role: p for p in meta.permissions}
		# Reception read/write, Technician read-only, Inspector read/write, Manager full
		self.assertTrue(roles["Garage Reception"].read and roles["Garage Reception"].write)
		self.assertTrue(roles["Garage Technician"].read and not roles["Garage Technician"].write)
		self.assertTrue(roles["Garage Inspector"].read and roles["Garage Inspector"].write)
		self.assertTrue(roles["Garage Manager"].read and roles["Garage Manager"].write)
		self.assertTrue(roles["Garage Supervisor"].read and roles["Garage Supervisor"].write)
