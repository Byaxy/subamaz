# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestAppointmentRequest(IntegrationTestCase):
	def test_create_appointment_request(self):
		doc = frappe.get_doc(
			{
				"doctype": "Appointment Request",
				"customer_name": "Test Customer",
				"phone": "+256700000001",
				"email": "test@example.com",
				"vehicle_registration": "UAX 123A",
				"preferred_date": frappe.utils.today(),
				"message": "Brake noise",
			}
		).insert()
		self.assertEqual(doc.status, "New")
		self.assertTrue(doc.name.startswith("APPT-"))

	def test_phone_stripped_on_validate(self):
		doc = frappe.get_doc(
			{
				"doctype": "Appointment Request",
				"customer_name": "Trim Test",
				"phone": "  +256700000002  ",
				"vehicle_registration": "UBB 456B",
			}
		).insert()
		self.assertEqual(doc.phone, "+256700000002")
