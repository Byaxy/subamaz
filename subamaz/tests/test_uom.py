# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestUOMFallback(IntegrationTestCase):
	def test_ltr_is_invalid_litre_is_canonical(self):
		self.assertFalse(frappe.db.exists("UOM", "Ltr"), "Ltr should not exist; canonical is Litre")
		self.assertTrue(
			frappe.db.exists("UOM", "Litre") or frappe.db.exists("UOM", "Nos"),
			"At least Litre or Nos should exist (Nos always via Stock Settings)",
		)

	def test_stock_uom_fallback_creates_item(self):
		item_group = frappe.db.get_value("Item Group", {}, "name") or "All Item Groups"
		stock_uom = frappe.db.get_value("UOM", {}, "name") or "Nos"
		self.assertIn(stock_uom, [r[0] for r in frappe.db.sql("select uom_name from tabUOM")])
		doc = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"Test-UOM-{frappe.generate_hash(length=4)}",
				"item_name": f"Test UOM {frappe.generate_hash(length=4)}",
				"item_group": item_group,
				"stock_uom": stock_uom,
				"is_stock_item": 0,
			}
		)
		doc.insert()
		self.assertEqual(doc.stock_uom, stock_uom)
