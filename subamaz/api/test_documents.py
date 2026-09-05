# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestDocuments(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Doc Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"DOC-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Doc",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
				"company": frappe.db.get_value("Company", {}, "name"),
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert()

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.doc_{frappe.generate_hash(length=4)}@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role,
					"send_welcome_email": 0,
					"user_type": "System User",
					"roles": [{"role": role}],
				}
			)
			user.insert(ignore_permissions=True)
		return email

	def _create_service_order(self):
		reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"reception_advisor": self.employee.name,
				"customer_complaint": "Doc test",
				"terms_accepted": 1,
				"photos": [
					{"photo": "/files/front.jpg", "photo_type": "Front"},
					{"photo": "/files/rear.jpg", "photo_type": "Rear"},
					{"photo": "/files/interior.jpg", "photo_type": "Interior"},
					{"photo": "/files/dashboard.jpg", "photo_type": "Dashboard"},
				],
			}
		).insert()
		reception.submit()
		so = frappe.get_doc(
			{
				"doctype": "Service Order",
				"customer": self.customer.name,
				"vehicle": self.vehicle.name,
				"vehicle_reception": reception.name,
				"opening_date": frappe.utils.today(),
			}
		).insert()
		so.submit()
		return so

	def test_send_document_print(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.documents import send_document

			so = self._create_service_order()
			result = send_document("Service Order", so.name, "print")
			self.assertEqual(result["channel"], "print")
			self.assertIn("html", result)
		finally:
			frappe.set_user("Administrator")

	def test_send_document_pdf(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.documents import send_document

			so = self._create_service_order()
			# pdf will set response, but we just check it doesn't throw
			try:
				send_document("Service Order", so.name, "pdf")
			except Exception as e:
				# pdf generation may fail if wkhtmltopdf missing, but should not be PermissionError
				self.assertNotIsInstance(e, frappe.PermissionError)
		finally:
			frappe.set_user("Administrator")

	def test_send_document_email_requires_recipient(self):
		user = self._create_user("Garage Manager")
		frappe.set_user(user)
		try:
			from subamaz.api.documents import send_document

			so = self._create_service_order()
			# without recipient and no contact, should throw
			self.assertRaises(frappe.ValidationError, send_document, "Service Order", so.name, "email", None)
			# with recipient should attempt send (mock)
			with patch("frappe.sendmail") as mock:
				result = send_document("Service Order", so.name, "email", "test@example.com")
				mock.assert_called_once()
				self.assertEqual(result["recipient"], "test@example.com")
		finally:
			frappe.set_user("Administrator")

	def test_send_document_guest_denied(self):
		frappe.set_user("Guest")
		try:
			from subamaz.api.documents import send_document

			self.assertRaises(frappe.PermissionError, send_document, "Service Order", "SO-001", "print")
		finally:
			frappe.set_user("Administrator")
