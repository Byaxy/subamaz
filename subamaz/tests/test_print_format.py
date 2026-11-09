# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase


class TestPrintFormatSandbox(SubamazTestCase):
	def test_print_format_sandbox_allows_get_single_value(self):
		from frappe.utils.jinja import render_template

		html = render_template('{{ frappe.db.get_single_value("Garage Branding Settings", "garage_name") or "SubaMaz" }}')
		self.assertIsInstance(html, str)
		self.assertTrue(len(html) > 0)

	def test_print_format_sandbox_blocks_get_single(self):
		from frappe.utils.jinja import render_template

		with self.assertRaises(Exception):
			render_template('{{ frappe.get_single("Garage Branding Settings").garage_name }}')

	def test_print_format_sandbox_blocks_get_singles_dict(self):
		from frappe.utils.jinja import render_template

		with self.assertRaises(Exception):
			render_template('{{ frappe.db.get_singles_dict("Garage Branding Settings") }}')

	def test_branded_print_formats_use_get_single_value(self):
		import json
		import pathlib

		fixtures_path = pathlib.Path(__file__).parents[1] / "fixtures" / "print_format.json"
		data = json.loads(fixtures_path.read_text())
		for fmt in data:
			html = fmt.get("html") or ""
			self.assertIn("frappe.db.get_single_value", html, f"{fmt.get('name')} should use get_single_value")
			self.assertNotIn("frappe.get_single", html, f"{fmt.get('name')} should not use frappe.get_single")
			self.assertNotIn("get_singles_dict", html, f"{fmt.get('name')} should not use get_singles_dict")

	def test_print_formats_exist_and_are_beta(self):
		import json

		for name, doctype, body_template in (
			("SubaMaz Sales Invoice", "Sales Invoice", "sales_invoice_body.html"),
			("SubaMaz Payment Receipt", "Payment Entry", "receipt_body.html"),
		):
			with self.subTest(print_format=name):
				doc = frappe.get_doc("Print Format", name)
				format_data = json.loads(doc.format_data)
				self.assertEqual(doc.doc_type, doctype)
				self.assertEqual(doc.standard, "Yes")
				self.assertEqual(doc.print_format_builder_beta, 1)
				self.assertEqual(doc.pdf_generator, "chrome")
				self.assertEqual(doc.page_number, "Hide")
				self.assertEqual(format_data["letter_head"], "SubaMaz Letter Head")
				self.assertEqual(format_data["page"], {"size": "A4", "orientation": "Portrait"})
				self.assertIn(body_template, format_data["sections"][0]["columns"][0]["fields"][0]["html"])

	def test_letter_head_is_not_default(self):
		doc = frappe.get_doc("Letter Head", "SubaMaz Letter Head")
		self.assertEqual(doc.source, "HTML")
		self.assertEqual(doc.footer_source, "HTML")
		self.assertEqual(doc.is_default, 0)
		self.assertIn("subamaz_header", doc.content)
		self.assertIn("subamaz_footer", doc.footer)
		self.assertIn("/assets/subamaz/css/print_formats.css", doc.custom_css)

	def test_default_print_formats(self):
		expected = {
			"Sales Invoice": "SubaMaz Sales Invoice",
			"Payment Entry": "SubaMaz Payment Receipt",
		}
		for doctype, print_format in expected.items():
			with self.subTest(doctype=doctype):
				values = frappe.get_all(
					"Property Setter",
					filters={
						"doc_type": doctype,
						"property": "default_print_format",
						"doctype_or_field": "DocType",
					},
					pluck="value",
				)
				self.assertIn(print_format, values)

	def test_print_format_templates_avoid_unsafe_jinja(self):
		import pathlib

		root = pathlib.Path(__file__).parents[1]
		template_dir = root / "templates" / "print_formats"
		for path in template_dir.rglob("*.html"):
			html = path.read_text()
			self.assertNotIn("frappe.get_single(", html, f"{path.name} uses frappe.get_single")
			self.assertNotIn("get_singles_dict", html, f"{path.name} uses get_singles_dict")
			self.assertNotIn("frappe.get_doc", html, f"{path.name} uses frappe.get_doc")

	def test_sales_invoice_body_renders_without_garage_data(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			currency="UGX",
			posting_date="2026-11-09",
			name="ACC-SINV-2026-00001",
			customer_name="Test Customer",
			customer_address=None,
			contact_mobile=None,
			contact_email=None,
			garage_vehicle=None,
			items=[
				frappe._dict(
					idx=1,
					item_name="Engine Oil",
					description="Engine Oil",
					item_code="OIL-001",
					qty=4,
					uom="Litre",
					rate=25000,
					amount=100000,
				)
			],
			taxes=[],
			total=100000,
			discount_amount=0,
			grand_total=130000,
			outstanding_amount=100000,
			paid_amount=30000,
			terms="",
			in_words="One Hundred Thirty Thousand Uganda Shillings Only",
		)
		html = render_template(
			"subamaz/templates/print_formats/partials/sales_invoice_body.html",
			{"doc": doc},
			is_path=True,
		)
		self.assertIn("INVOICE", html)
		self.assertIn(doc.name, html)
		self.assertIn("Test Customer", html)
		self.assertIn("130,000", html)
		self.assertIn("BALANCE DUE", html)

	def test_payment_receipt_body_renders_without_references(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			paid_from_account_currency="UGX",
			paid_to_account_currency="UGX",
			party_type="Customer",
			party=None,
			party_name="Test Customer",
			contact_email=None,
			posting_date="2026-11-09",
			name="PE-2026-00001",
			paid_amount=130000,
			unallocated_amount=0,
			mode_of_payment="Cash",
			reference_no=None,
			reference_date=None,
			references=[],
			in_words="One Hundred Thirty Thousand Uganda Shillings Only",
		)
		html = render_template(
			"subamaz/templates/print_formats/partials/receipt_body.html",
			{"doc": doc},
			is_path=True,
		)
		self.assertIn("PAYMENT RECEIPT", html)
		self.assertIn(doc.name, html)
		self.assertIn("Advance payment", html)
		self.assertIn("BALANCE DUE", html)

	def test_new_print_format_assets_avoid_legacy_gold(self):
		import pathlib

		root = pathlib.Path(__file__).parents[1]
		paths = [
			*(root / "templates" / "print_formats").rglob("*.html"),
			root / "public" / "css" / "print_formats.css",
			root / "subamaz" / "print_format" / "suba_sales_invoice" / "suba_sales_invoice.json",
			root / "subamaz" / "print_format" / "suba_payment_receipt" / "suba_payment_receipt.json",
		]
		for path in paths:
			self.assertNotIn("#C9A227", path.read_text().upper(), f"{path.name} uses legacy gold")
