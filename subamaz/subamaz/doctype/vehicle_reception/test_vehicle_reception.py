# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer", "Employee"]

PHOTO_TYPES = ("Front", "Rear", "Interior", "Dashboard")


class TestVehicleReception(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Rec Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.employee = self._make_employee()
		self.vehicle = self._make_vehicle().insert()

	def _make_employee(self):
		return frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Reception",
				"last_name": f"Advisor {frappe.generate_hash(length=4)}",
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
				"registration_number": f"VR-{suffix}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"current_mileage": 10000,
			}
		)

	def _make_reception(self, **overrides):
		doc = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "Grinding noise when braking",
				"terms_accepted": 1,
				"damage_markers": [
					{"panel": "Front Bumper", "damage_type": "Scratch", "severity": "Minor"}
				],
				"accessories": [{"accessory_name": "Spare Tire", "present": 1}],
				"personal_belongings": [{"belonging_name": "Child Seat"}],
				"photos": [{"photo": f"/files/{t.lower()}.jpg", "photo_type": t} for t in PHOTO_TYPES],
			}
		)
		doc.update(overrides)
		return doc

	def test_naming_series(self):
		doc = self._make_reception().insert()
		self.assertRegex(doc.name, r"^VR-\d{4}-\d{5}$")

	def test_submit_requires_terms(self):
		doc = self._make_reception(terms_accepted=0).insert()
		self.assertRaises(frappe.ValidationError, doc.submit)

	def test_missing_required_photo_blocks_submit(self):
		doc = self._make_reception()
		doc.photos = [row for row in doc.photos if row.photo_type != "Interior"]
		doc.insert()
		with self.assertRaises(frappe.ValidationError) as exc:
			doc.submit()
		self.assertIn("Interior", str(exc.exception))

	def test_successful_submit_passes_all_guards(self):
		doc = self._make_reception().insert()
		doc.submit()
		self.assertEqual(doc.docstatus, 1)

	def test_vehicle_status_set_on_submit(self):
		doc = self._make_reception().insert()
		doc.submit()
		self.assertEqual(
			frappe.db.get_value("Garage Vehicle", self.vehicle.name, "current_status"), "Received"
		)

	def test_complaint_preserved_after_submit(self):
		doc = self._make_reception().insert()
		doc.submit()
		stored = frappe.db.get_value("Vehicle Reception", doc.name, "customer_complaint")
		self.assertEqual(stored, "Grinding noise when braking")

	def test_complaint_cannot_be_changed_on_amendment(self):
		doc = self._make_reception().insert()
		doc.submit()
		doc.cancel()
		amended = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"amended_from": doc.name,
				"customer": doc.customer,
				"vehicle": doc.vehicle,
				"reception_advisor": doc.reception_advisor,
				"customer_complaint": "Changed after the fact",
				"terms_accepted": 1,
				"photos": [{"photo": "/files/front.jpg", "photo_type": "Front"}],
			}
		)
		self.assertRaises(frappe.ValidationError, amended.insert)

	def test_parked_draft_stays_unsubmitted(self):
		doc = self._make_reception(status="Draft — Parked").insert()
		self.assertEqual(doc.docstatus, 0)
		self.assertEqual(doc.status, "Draft — Parked")

	def test_submitted_status_rejected_on_draft(self):
		doc = self._make_reception(status="Submitted")
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_customer_vehicle_mismatch_blocked(self):
		other_customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Mismatch {frappe.generate_hash(length=4)}"}
		).insert()
		doc = self._make_reception(customer=other_customer.name)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_child_rows_validate_select_options(self):
		doc = self._make_reception()
		doc.damage_markers[0].panel = "Sunroof"
		self.assertRaises(frappe.ValidationError, doc.insert)
