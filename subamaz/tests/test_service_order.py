# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestServiceOrderCross(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"SOCross Cust {frappe.generate_hash(length=4)}"}
		).insert()
		self.vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"SC-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer.name,
				"current_mileage": 12000,
			}
		).insert()
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "SOCross",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
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
				"customer_complaint": "Brake issue",
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

	def test_auto_project_by_duration(self):
		from frappe.utils import add_days, today

		expected_finish = add_days(today(), 30)
		doc = self._make_so(expected_finish=expected_finish, estimated_total=0).insert()
		doc.submit()
		# trigger after_submit logic
		doc.reload()
		# on_update_after_submit is called on save after submit — simulate update
		doc.expected_finish = expected_finish
		doc.save()
		doc.reload()
		self.assertTrue(doc.project)
		first = doc.project
		# idempotent — second save should not create new project
		doc.save()
		doc.reload()
		self.assertEqual(doc.project, first)
		self.assertTrue(frappe.db.exists("Project", first))

	def test_auto_quotation_when_estimated_total(self):
		doc = self._make_so(estimated_total=0).insert()
		# set estimated via labour/parts to trigger compute
		doc.estimated_labour = 1000
		doc.estimated_parts = 500
		doc.save()
		doc.submit()
		doc.reload()
		# trigger ensure_quotation via on_update_after_submit
		doc.save()
		doc.reload()
		self.assertTrue(doc.quotation)
		first = doc.quotation
		doc.save()
		doc.reload()
		self.assertEqual(doc.quotation, first)
		self.assertTrue(frappe.db.exists("Quotation", first))

	def test_rollup_mocked_job_cards(self):
		from subamaz.subamaz.doctype.service_order.service_order import recompute_rollup

		doc = self._make_so().insert()
		doc.submit()
		fake_cards = [
			{"name": "JC-001", "estimated_cost": 1000, "completion_percent": 50},
			{"name": "JC-002", "estimated_cost": 2000, "completion_percent": 100},
		]
		original_get_all = frappe.get_all

		def get_all_side_effect(doctype, *args, **kwargs):
			if doctype == "Garage Job Card":
				return fake_cards
			if doctype in ("Time Log Entry", "Consumed Part Entry"):
				return []
			return original_get_all(doctype, *args, **kwargs)

		def exists_side_effect(doctype, name=None):
			if doctype == "DocType" and name in ("Garage Job Card", "Time Log Entry", "Consumed Part Entry"):
				return True
			if doctype == "Service Order" and isinstance(name, str):
				return frappe.db.exists(doctype, name)
			if doctype == "DocType":
				return frappe.db.exists(doctype, name)
			return True

		with patch("frappe.db.exists", side_effect=exists_side_effect):
			with patch("frappe.get_all", side_effect=get_all_side_effect):
				recompute_rollup(doc.name)
		doc.reload()
		self.assertAlmostEqual(doc.estimated_labour, 3000, delta=1)
		self.assertGreater(doc.completion_percent, 80)

	def test_timeline_helper_visible_flag(self):
		from subamaz.subamaz.doctype.service_order.service_order import add_timeline_entry

		doc = self._make_so().insert()
		add_timeline_entry(doc.name, "Customer called", "Customer Communication", visible=True)
		add_timeline_entry(doc.name, "Internal note", "Note", visible=False)
		reloaded = frappe.get_doc("Service Order", doc.name)
		self.assertEqual(len(reloaded.timeline), 2)
		self.assertEqual(reloaded.timeline[0].visible_to_customer, 1)
		self.assertEqual(reloaded.timeline[1].visible_to_customer, 0)

	def test_vehicle_linkage_on_submit(self):
		doc = self._make_so().insert()
		doc.submit()
		linked = frappe.db.get_value("Garage Vehicle", self.vehicle.name, "current_service_order")
		self.assertEqual(linked, doc.name)

	def test_workflow_exists_and_active(self):
		workflow = frappe.get_doc("Workflow", "Service Order Workflow")
		self.assertEqual(workflow.document_type, "Service Order")
		self.assertEqual(workflow.workflow_state_field, "status")
		self.assertTrue(workflow.is_active)

	def test_permissions_reception_vs_technician(self):
		meta = frappe.get_meta("Service Order")
		reception = next(p for p in meta.permissions if p.role == "Garage Reception")
		tech = next(p for p in meta.permissions if p.role == "Garage Technician")
		self.assertTrue(reception.write)
		self.assertFalse(tech.write)
