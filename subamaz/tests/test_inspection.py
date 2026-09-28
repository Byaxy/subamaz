# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

from unittest.mock import patch

import frappe

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestInspectionCrossDoctype(SubamazTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"InspX Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"IX-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"current_mileage": 15000,
			}
		).insert()
		self.inspector = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Inspect",
				"last_name": f"Cross {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
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
				"mileage": 15000,
				"checklist": [
					{"section": "Engine", "checklist_item": "Oil Leak", "result": "Pass"},
				],
				"inspection_result": "Good",
				"recommendation": "Safe to Drive",
				"notes": "All good",
			}
		)
		doc.update(overrides)
		return doc

	def test_pdf_render_returns_bytes(self):
		doc = self._make_inspection().insert()
		doc.submit()
		with patch("frappe.utils.pdf.get_pdf", return_value=b"%PDF-1.4 fake"):
			pdf = doc.get_pdf()
		self.assertIsNotNone(pdf)
		self.assertTrue(pdf.startswith(b"%PDF"))

	def test_email_sent_when_contact_exists(self):
		email = f"insp.{frappe.generate_hash(length=4)}@example.com"
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": f"InspContact {frappe.generate_hash(length=4)}",
				"email_id": email,
				"email_ids": [{"email_id": email, "is_primary": 1}],
				"links": [{"link_doctype": "Customer", "link_name": self.customer.name}],
			}
		).insert()
		# ensure email_id persisted via child table sync
		contact.reload()
		doc = self._make_inspection().insert()
		with patch("frappe.sendmail") as mock_send, patch.object(
			doc.__class__, "get_pdf", return_value=b"%PDF"
		):
			doc.submit()
			mock_send.assert_called_once()
			_kwargs = mock_send.call_args.kwargs
			self.assertIn(contact.email_id, _kwargs.get("recipients", []))

	def test_email_no_crash_when_no_contact(self):
		doc = self._make_inspection().insert()
		with patch("frappe.sendmail") as mock_send:
			# should not raise even without contact
			doc.submit()
			mock_send.assert_not_called()

	def test_timeline_no_crash_when_no_service_order(self):
		doc = self._make_inspection().insert()
		# vehicle has no current_service_order
		frappe.db.set_value("Garage Vehicle", self.vehicle.name, "current_service_order", "")
		doc.submit()
		self.assertEqual(doc.docstatus, 1)

	def test_timeline_guarded_when_no_service_order_doctype(self):
		# Service Order / Service Timeline Entry don't exist in phase 05 — must no-op
		doc = self._make_inspection().insert()
		frappe.db.set_value("Garage Vehicle", self.vehicle.name, "current_service_order", "SO-FAKE")
		# Should still succeed without throwing even though Service Order doctype missing
		doc.submit()
		self.assertEqual(doc.docstatus, 1)

	def test_permissions_inspector_can_submit(self):
		meta = frappe.get_meta("Vehicle Inspection")
		inspector_perms = [p for p in meta.permissions if p.role == "Garage Inspector"]
		self.assertTrue(inspector_perms)
		perms = inspector_perms[0]
		self.assertTrue(perms.read)
		self.assertTrue(perms.write)
		self.assertTrue(perms.create)
		self.assertTrue(perms.submit)

	def test_permissions_technician_read_only(self):
		meta = frappe.get_meta("Vehicle Inspection")
		tech_perms = [p for p in meta.permissions if p.role == "Garage Technician"]
		self.assertTrue(tech_perms)
		perms = tech_perms[0]
		self.assertTrue(perms.read)
		self.assertFalse(perms.write)
		self.assertFalse(perms.submit)

	def test_vehicle_current_service_order_field_exists(self):
		meta = frappe.get_meta("Garage Vehicle")
		field = meta.get_field("current_service_order")
		self.assertIsNotNone(field)
		self.assertEqual(field.fieldtype, "Link")
		self.assertEqual(field.options, "Service Order")
