# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from subamaz import report_customizer
from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestVehicleSales(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.company = frappe.db.get_value("Company", {}, "name")
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Veh Sales {frappe.generate_hash(length=4)}"}
		).insert()
		self.item = self._get_service_item()

	def _get_service_item(self):
		code = frappe.db.get_value("Item", {"is_stock_item": 0}, "name")
		if code:
			return code
		return frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"VehSvc-{frappe.generate_hash(length=4)}",
				"item_name": "Vehicle Service",
				"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
				"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
				"is_stock_item": 0,
			}
		).insert().name

	def _make_vehicle(self, customer, registration_number=None, make="Toyota", type="SUV", model="RAV4"):
		return frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": registration_number or f"VS-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": customer,
				"make": make,
				"type": type,
				"model": model,
			}
		).insert()

	def _make_sales_order(self, vehicle):
		from frappe.utils import add_days, nowdate

		currency = frappe.db.get_value("Company", self.company, "default_currency") or "USD"
		so = frappe.new_doc("Sales Order")
		so.company = self.company
		so.customer = self.customer.name
		so.currency = currency
		so.conversion_rate = 1
		so.price_list_currency = currency
		so.plc_conversion_rate = 1
		so.delivery_date = add_days(nowdate(), 7)
		so.garage_vehicle = vehicle.name
		so.append("items", {"item_code": self.item, "qty": 1, "rate": 100, "delivery_date": so.delivery_date})
		return so.insert().submit()

	def test_custom_fields_exist_on_sales_docs(self):
		for dt in ("Sales Order", "Sales Invoice"):
			field = frappe.get_meta(dt).get_field("garage_vehicle")
			self.assertIsNotNone(field, f"{dt} missing garage_vehicle field")
			self.assertEqual(field.fieldtype, "Link")
			self.assertEqual(field.options, "Garage Vehicle")
		custom_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": ["in", ["Sales Order", "Sales Invoice"]], "fieldname": "garage_vehicle"},
			fields=["dt", "module"],
		)
		self.assertEqual(len(custom_fields), 2)
		for cf in custom_fields:
			self.assertEqual(cf.module, "Subamaz")

	def test_hooks_export_fixtures_covers_vehicle_fields(self):
		entries = [f for f in frappe.get_hooks("fixtures") or [] if f.get("doctype") == "Custom Field"]
		self.assertTrue(
			any(f.get("filters", {}).get("module") == "Subamaz" for f in entries),
			"hooks fixtures must keep the module-scoped Custom Field entry",
		)

	def test_sales_invoice_carries_vehicle_from_order(self):
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

		vehicle = self._make_vehicle(self.customer.name)
		so = self._make_sales_order(vehicle)
		si = make_sales_invoice(so.name)
		self.assertEqual(si.garage_vehicle, vehicle.name)

	def test_vehicle_lookup_scopes_to_customer(self):
		other_customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Veh Other {frappe.generate_hash(length=4)}"}
		).insert()
		mine = self._make_vehicle(self.customer.name)
		self._make_vehicle(other_customer.name)
		names = frappe.get_all("Garage Vehicle", filters={"customer": self.customer.name}, pluck="name")
		self.assertIn(mine.name, names)
		self.assertEqual(len(names), 1)

	def test_report_customizer_adds_vehicle_columns(self):
		result = {
			"columns": [
				{"label": "Voucher", "fieldname": "voucher_no", "fieldtype": "Data", "width": 120},
				{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 120},
			],
			"result": [
				{"voucher_no": "SI-001", "voucher_type": "Sales Invoice", "customer_name": "C1"},
				{"voucher_no": "PE-001", "voucher_type": "Payment Entry", "customer_name": "C1"},
			],
		}
		invoice_rows = [{"name": "SI-001", "garage_vehicle": "GV-001"}]
		vehicle_rows = [
			{
				"name": "GV-001",
				"registration_number": "REG-001",
				"make": "Toyota",
				"type": "SUV",
				"model": "RAV4",
				"year": 2021,
			}
		]

		def fake_get_all(doctype, filters=None, fields=None, pluck=None):
			if doctype == "Sales Invoice":
				return invoice_rows
			if doctype == "Garage Vehicle":
				return vehicle_rows
			return []

		with mock.patch.object(frappe, "get_all", side_effect=fake_get_all):
			out = report_customizer._apply_vehicle_columns(
				result, report_customizer.REPORT_CONFIG["Sales Register"]
			)

		fieldnames = [c["fieldname"] for c in out["columns"]]
		self.assertEqual(
			fieldnames,
			[
				"voucher_no",
				"customer_name",
				"vehicle_registration",
				"vehicle_make",
				"vehicle_type",
				"vehicle_model",
				"vehicle_year",
			],
		)
		row = out["result"][0]
		self.assertEqual(row["vehicle_registration"], "REG-001")
		self.assertEqual(row["vehicle_make"], "Toyota")
		self.assertEqual(row["vehicle_type"], "SUV")
		self.assertEqual(row["vehicle_model"], "RAV4")
		self.assertEqual(row["vehicle_year"], 2021)
		# Non-invoice rows (payments, totals) are left untouched.
		self.assertNotIn("vehicle_registration", out["result"][1])

	def test_report_customizer_unknown_report_passthrough(self):
		result = {"columns": [], "result": []}
		self.assertIs(
			report_customizer._apply_vehicle_columns(result, report_customizer.REPORT_CONFIG["Sales Register"]),
			result,
		)
