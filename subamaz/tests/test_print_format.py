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
			("SubaMaz Sales Invoice", "Sales Invoice", "sales_invoice.html"),
			("SubaMaz Payment Receipt", "Receipt", "receipt.html"),
			("SubaMaz Pro-Forma Invoice", "Quotation", "proforma_invoice.html"),
			("SubaMaz Purchase Order", "Purchase Order", "purchase_order.html"),
			("SubaMaz Request for Quotation", "Request for Quotation", "request_for_quotation.html"),
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

	def test_letter_head_is_default(self):
		doc = frappe.get_doc("Letter Head", "SubaMaz Letter Head")
		self.assertEqual(doc.source, "HTML")
		self.assertEqual(doc.footer_source, "HTML")
		self.assertEqual(doc.is_default, 1)
		self.assertIn("subamaz_header", doc.content)
		self.assertIn("subamaz_footer", doc.footer)
		self.assertIn("/assets/subamaz/css/print_formats.css", doc.custom_css)

	def test_default_print_formats(self):
		expected = {
			"Sales Invoice": "SubaMaz Sales Invoice",
			"Receipt": "SubaMaz Payment Receipt",
			"Quotation": "SubaMaz Pro-Forma Invoice",
			"Purchase Order": "SubaMaz Purchase Order",
			"Request for Quotation": "SubaMaz Request for Quotation",
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

		payment_entry_values = frappe.get_all(
			"Property Setter",
			filters={
				"doc_type": "Payment Entry",
				"property": "default_print_format",
				"doctype_or_field": "DocType",
			},
			pluck="value",
		)
		self.assertNotIn("SubaMaz Payment Receipt", payment_entry_values)

	def test_payment_entry_receipt_fields_are_fixture_scoped(self):
		import json
		import pathlib

		root = pathlib.Path(__file__).parents[1]
		fields = {
			row["name"]: row
			for row in json.loads((root / "fixtures" / "custom_field.json").read_text())
		}
		for name in ("Payment Entry-custom_receipt", "Payment Entry-check_bank"):
			with self.subTest(field=name):
				self.assertIn(name, fields)
				self.assertEqual(fields[name]["module"], "Subamaz")

		custom_field_hooks = [
			hook
			for hook in frappe.get_hooks("fixtures")
			if isinstance(hook, dict) and hook.get("doctype") == "Custom Field"
		]
		self.assertTrue(
			any(hook.get("filters", {}).get("module") == "Subamaz" for hook in custom_field_hooks)
		)

	def test_print_format_templates_avoid_unsafe_jinja(self):
		import pathlib

		root = pathlib.Path(__file__).parents[1]
		template_dir = root / "templates" / "print_formats"
		self.assertFalse((template_dir / "partials").exists())
		for path in template_dir.rglob("*.html"):
			html = path.read_text()
			self.assertNotIn("frappe.get_single(", html, f"{path.name} uses frappe.get_single")
			self.assertNotIn("get_singles_dict", html, f"{path.name} uses get_singles_dict")
			self.assertNotIn("frappe.get_doc", html, f"{path.name} uses frappe.get_doc")

	def test_item_description_appends_code_only_when_different(self):
		from frappe.utils.jinja import render_template

		template = (
			'{% from "subamaz/templates/print_formats/macros.html" import subamaz_item_description %}'
			"{{ subamaz_item_description(item) }}"
		)
		cases = (
			({"item_name": "Brake Pad", "item_code": "SP-1042"}, "Brake Pad - SP-1042"),
			({"item_name": "Brake Pad", "item_code": "BRAKE PAD"}, "Brake Pad"),
			({"item_name": None, "item_code": "SP-1042"}, "SP-1042"),
			({"item_name": "Generic Part", "item_code": None}, "Generic Part"),
			(
				{"item_name": "Brake Pad", "description": "Ignored", "item_code": "SP-1042"},
				"Brake Pad - SP-1042",
			),
		)
		for values, expected in cases:
			with self.subTest(values=values):
				html = render_template(template, {"item": frappe._dict(values)}, is_path=False)
				self.assertEqual(html.strip(), expected)

	def test_legacy_print_formats_removed(self):
		for name in ("Garage Invoice", "Garage Quotation", "Job Sheet"):
			with self.subTest(print_format=name):
				self.assertFalse(frappe.db.exists("Print Format", name))
		self.assertTrue(frappe.db.exists("Print Format", "Delivery Note"))
		self.assertTrue(frappe.db.exists("Print Format", "Vehicle Inspection Report"))

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
			taxes=[frappe._dict(description="VAT", tax_amount=26000)],
			total=100000,
			discount_amount=0,
			total_taxes_and_charges=26000,
			grand_total=130000,
			outstanding_amount=100000,
			paid_amount=30000,
			terms="",
			in_words="One Hundred Thirty Thousand Uganda Shillings Only",
		)
		html = render_template(
			"subamaz/templates/print_formats/sales_invoice.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)
		self.assertIn("INVOICE", html)
		self.assertIn(doc.name, html)
		self.assertIn("Test Customer", html)
		self.assertIn("130,000", html)
		self.assertIn("BALANCE DUE", html)
		self.assertIn("Tax", html)
		self.assertIn("26,000", html)
		self.assertIn("Amount in Words", html)
		self.assertIn("One Hundred Thirty Thousand Uganda Shillings Only", html)
		self.assertIn("<span>Discount</span><span>0</span>", html)
		self.assertIn("Engine Oil - OIL-001", html)
		self.assertNotIn("VAT", html)

	def test_sales_invoice_body_shows_non_zero_discount(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			currency="UGX",
			posting_date="2026-11-09",
			name="ACC-SINV-2026-00002",
			customer_name="Test Customer",
			customer_address=None,
			contact_mobile=None,
			contact_email=None,
			garage_vehicle=None,
			items=[],
			taxes=[],
			total=100000,
			discount_amount=5000,
			total_taxes_and_charges=0,
			grand_total=95000,
			outstanding_amount=95000,
			paid_amount=0,
			terms="",
		)
		html = render_template(
			"subamaz/templates/print_formats/sales_invoice.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)
		self.assertIn("<span>Discount</span><span>-5,000</span>", html)
		self.assertIn("Ninety Five Thousand", html)

	def test_proforma_invoice_body_renders_without_vehicle(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			currency="UGX",
			transaction_date="2026-11-09",
			valid_till="2026-12-09",
			name="SAL-QTN-2026-00001",
			quotation_to="Customer",
			party_name="Test Customer",
			customer_name="Test Customer",
			customer_address=None,
			contact_mobile="0700000000",
			contact_email="customer@example.com",
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
			taxes=[frappe._dict(description="VAT", tax_amount=26000)],
			total=100000,
			discount_amount=0,
			total_taxes_and_charges=26000,
			grand_total=130000,
			terms="",
		)
		html = render_template(
			"subamaz/templates/print_formats/proforma_invoice.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)
		self.assertIn("PRO-FORMA INVOICE", html)
		self.assertIn(doc.name, html)
		self.assertIn("Test Customer", html)
		self.assertIn("09-12-2026", html)
		self.assertIn("Valid Until", html)
		self.assertIn("130,000", html)
		self.assertIn("not a tax invoice", html)
		self.assertIn("Tax", html)
		self.assertIn("26,000", html)
		self.assertIn("Amount in Words", html)
		self.assertIn("One Hundred And Thirty Thousand", html)
		self.assertIn("<span>Discount</span><span>0</span>", html)
		self.assertIn("Engine Oil - OIL-001", html)
		self.assertNotIn("VAT", html)
		self.assertNotIn("BALANCE DUE", html)

	def test_purchase_order_body_renders_with_advance(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			currency="UGX",
			transaction_date="2026-11-09",
			schedule_date="2026-11-20",
			name="PUR-ORD-2026-00001",
			supplier="Test Supplier",
			supplier_name="Test Supplier",
			supplier_address=None,
			contact_mobile=None,
			contact_email="supplier@example.com",
			order_confirmation_no="SUP-REF-1",
			items=[
				frappe._dict(
					idx=1,
					item_name="Brake Pad",
					description="Brake Pad",
					item_code="BRK-001",
					qty=2,
					uom="Nos",
					rate=50000,
					amount=100000,
				)
			],
			taxes=[frappe._dict(description="VAT", tax_amount=30000)],
			total=100000,
			discount_amount=0,
			total_taxes_and_charges=30000,
			grand_total=130000,
			advance_paid=50000,
			terms="",
		)
		html = render_template(
			"subamaz/templates/print_formats/purchase_order.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)
		self.assertIn("PURCHASE ORDER", html)
		self.assertIn(doc.name, html)
		self.assertIn("Test Supplier", html)
		self.assertIn("20-11-2026", html)
		self.assertIn("SUP-REF-1", html)
		self.assertIn("130,000", html)
		self.assertIn("Advance Paid", html)
		self.assertIn("BALANCE PAYABLE", html)
		self.assertIn("80,000", html)
		self.assertIn("Tax", html)
		self.assertIn("30,000", html)
		self.assertIn("Amount in Words", html)
		self.assertIn("One Hundred And Thirty Thousand", html)
		self.assertIn("<span>Discount</span><span>0</span>", html)
		self.assertIn("Brake Pad - BRK-001", html)
		self.assertNotIn("VAT", html)

	def test_request_for_quotation_uses_first_supplier_only(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			name="PUR-RFQ-2026-00001",
			transaction_date="2026-11-09",
			schedule_date="2026-11-20",
			company="SubaMaz Auto",
			incoterm=None,
			message_for_supplier="",
			terms="",
			suppliers=[
				frappe._dict(
					supplier="SUP-1",
					supplier_name="First Supplier",
					contact=None,
					email_id="first@example.com",
				),
				frappe._dict(
					supplier="SUP-2",
					supplier_name="Second Supplier",
					contact=None,
					email_id="second@example.com",
				),
			],
			items=[
				frappe._dict(
					idx=1,
					item_name="Oil Filter",
					description="Oil Filter",
					item_code="FLT-001",
					qty=10,
					uom="Nos",
				)
			],
		)
		html = render_template(
			"subamaz/templates/print_formats/request_for_quotation.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)
		self.assertIn("REQUEST FOR QUOTATION", html)
		self.assertIn(doc.name, html)
		self.assertIn("First Supplier", html)
		self.assertIn("first@example.com", html)
		self.assertNotIn("Second Supplier", html)
		self.assertNotIn("second@example.com", html)
		self.assertIn("20-11-2026", html)
		self.assertIn("Please supply", html)
		self.assertIn("Oil Filter - FLT-001", html)
		self.assertNotIn("UNIT PRICE", html)
		self.assertNotIn("AMOUNT", html)

	def test_receipt_body_renders_snapshot_balances(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			currency="UGX",
			receipt_date="2026-11-09",
			name="RCPT-2026-00001",
			customer_name="Test Customer",
			customer_address=None,
			billing_address=None,
			amount_in_words="One Hundred Thirty Thousand Uganda Shillings Only",
			total_amount_due=130000,
			total_amount_received=30000,
			total_balance_due=100000,
			customer_total_outstanding=250000,
			receipt_payments=[
				frappe._dict(
					sales_invoice="ACC-SINV-2026-00001",
					invoice_date="2026-11-01",
					amount_due=130000,
					amount_received=30000,
					balance_due=100000,
				)
			],
			receipt_payment_methods=[
				frappe._dict(
					payment_method="Cash",
					check_bank=None,
					bank_name=None,
					reference_no=None,
					reference_date=None,
					amount=30000,
				)
			],
		)
		html = render_template(
			"subamaz/templates/print_formats/receipt.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)
		self.assertIn("PAYMENT RECEIPT", html)
		self.assertIn(doc.name, html)
		self.assertIn("Test Customer", html)
		self.assertIn("One Hundred Thirty Thousand Uganda Shillings Only", html)
		self.assertIn("ACC-SINV-2026-00001", html)
		self.assertIn("130,000", html)
		self.assertIn("30,000", html)
		self.assertIn("100,000", html)
		self.assertIn("250,000", html)
		self.assertIn("Cash", html)
		self.assertIn("Cash (UGX)", html)
		self.assertIn("Mobile Money (UGX)", html)
		self.assertIn("Cheque / Bank (UGX)", html)
		self.assertIn("Total Amount (UGX)", html)
		self.assertIn("Total Amount Due:", html)
		self.assertIn("Total Amount Paid:", html)
		self.assertIn("Balance Due:", html)
		self.assertIn("Total Outstanding:", html)
		self.assertIn(
			'<div class="suba-total-line"><span>Total Amount Paid:</span>',
			html,
		)
		self.assertIn(
			'<div class="suba-grand-total suba-outstanding-total"><span>Total Outstanding:</span>',
			html,
		)
		self.assertLess(html.index("Total Amount Due:"), html.index("Total Amount Paid:"))
		self.assertLess(html.index("Total Amount Paid:"), html.index("Balance Due:"))
		self.assertLess(html.index("Balance Due:"), html.index("Total Outstanding:"))

	def test_receipt_payment_methods_groups_cash_mobile_bank(self):
		import pathlib

		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			currency="UGX",
			receipt_date="2026-11-09",
			name="RCPT-2026-00003",
			customer_name="Test Customer",
			customer_address=None,
			billing_address=None,
			amount_in_words="Fifty Thousand Uganda Shillings Only",
			total_amount_due=50000,
			total_amount_received=50000,
			total_balance_due=0,
			customer_total_outstanding=100000,
			receipt_payments=[
				frappe._dict(
					sales_invoice="ACC-SINV-2026-00003",
					invoice_date="2026-11-01",
					amount_due=50000,
					amount_received=50000,
					balance_due=0,
				)
			],
			receipt_payment_methods=[
				frappe._dict(payment_method="Cash", amount=10000),
				frappe._dict(payment_method="Mobile Money", amount=15000),
				frappe._dict(
					payment_method="Bank",
					check_bank="Test Bank",
					reference_no="CHQ-001",
					amount=20000,
				),
				frappe._dict(
					payment_method="Bank",
					check_bank="Test Bank",
					reference_no="CHQ-002",
					amount=5000,
				),
			],
		)
		html = render_template(
			"subamaz/templates/print_formats/receipt.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)

		self.assertIn("Cash (UGX)", html)
		self.assertIn("Mobile Money (UGX)", html)
		self.assertIn("Cheque / Bank (UGX)", html)
		self.assertIn("Total Amount (UGX)", html)
		self.assertIn(
			'<td rowspan="2" class="suba-cell-center suba-cell-strong">UGX 10,000</td>',
			html,
		)
		self.assertIn(
			'<td rowspan="2" class="suba-cell-center suba-cell-strong">UGX 15,000</td>',
			html,
		)
		self.assertIn("UGX 20,000", html)
		self.assertIn("UGX 5,000", html)
		self.assertIn("UGX 50,000", html)
		self.assertIn("Test Bank", html)
		self.assertIn("CHQ-001", html)
		self.assertIn("CHQ-002", html)
		self.assertNotIn("Reference Date", html)

		css = (
			pathlib.Path(__file__).parents[1] / "public" / "css" / "print_formats.css"
		).read_text()
		self.assertIn(".suba-methods-table", css)
		self.assertIn("margin-top: 4mm;", css)
		self.assertIn("border-left: 0.25mm solid #cbd5e1;", css)

	def test_receipt_body_renders_advance_without_invoice(self):
		from frappe.utils.jinja import render_template

		doc = frappe._dict(
			currency="UGX",
			receipt_date="2026-11-09",
			name="RCPT-2026-00002",
			customer_name="Test Customer",
			customer_address=None,
			billing_address=None,
			amount_in_words="Fifty Thousand Uganda Shillings Only",
			total_amount_due=0,
			total_amount_received=50000,
			total_balance_due=0,
			customer_total_outstanding=0,
			receipt_payments=[
				frappe._dict(
					sales_invoice=None,
					invoice_date=None,
					amount_due=0,
					amount_received=50000,
					balance_due=0,
				)
			],
			receipt_payment_methods=[],
		)
		html = render_template(
			"subamaz/templates/print_formats/receipt.html",
			{"doc": doc, "letter_head": "", "footer": ""},
			is_path=True,
		)
		self.assertIn("Advance / On account", html)
		self.assertIn("50,000", html)
		self.assertIn("Balance Due:", html)
		self.assertIn("Total Outstanding:", html)

	def test_new_print_format_assets_avoid_legacy_gold(self):
		import pathlib

		root = pathlib.Path(__file__).parents[1]
		paths = [
			*(root / "templates" / "print_formats").rglob("*.html"),
			root / "public" / "css" / "print_formats.css",
			*(root / "subamaz" / "print_format").rglob("*.json"),
		]
		for path in paths:
			self.assertNotIn("#C9A227", path.read_text().upper(), f"{path.name} uses legacy gold")

	def test_desk_preview_releases_bottom_on_multi_page(self):
		import pathlib

		root = pathlib.Path(__file__).parents[1]
		script = (root / "templates" / "print_formats" / "print_layout_script.html").read_text()
		css = (root / "public" / "css" / "print_formats.css").read_text()
		self.assertIn('classList.toggle("suba-multi-page", multiPage)', script)
		self.assertIn("pages > 1 || bottomHeight + 2 > remaining", script)
		self.assertIn("body.print-format-doc.suba-multi-page .suba-bottom", css)
		self.assertIn("margin-top: 0 !important;", css)
		self.assertIn("wrapClosing", script)
		self.assertIn("suba-closing--new-page", script)
		self.assertIn(".suba-closing.suba-closing--new-page", css)
		self.assertIn("justify-content: space-between;", css)
		self.assertIn("height: calc(var(--suba-page-body-height) - 1mm);", css)
		self.assertNotIn(".suba-bottom.suba-bottom--new-page", css)
