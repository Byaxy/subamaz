# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

from unittest.mock import patch

import frappe

from subamaz.subamaz.doctype.receipt.receipt import (
	create_receipt_from_pe,
	get_payment_entry_details,
)
from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Account",
	"Address",
	"Bank",
	"Company",
	"Currency",
	"Customer",
	"Mode of Payment",
	"Payment Entry",
	"Sales Invoice",
]


class TestReceipt(SubamazTestCase):
	def _receipt(self, **kwargs):
		doc = frappe.new_doc("Receipt")
		doc.company = kwargs.get("company") or frappe.get_all("Company", pluck="name")[0]
		doc.currency = kwargs.get("currency") or frappe.db.get_value(
			"Company", doc.company, "default_currency"
		)
		doc.customer = kwargs.get("customer") or "Test Customer"
		doc.receipt_date = kwargs.get("receipt_date") or "2026-11-09"
		for row in kwargs.get("payments") or []:
			doc.append("receipt_payments", row)
		return doc

	def _payment_entry(self, **kwargs):
		return frappe._dict(
			name=kwargs.get("name") or "PE-2026-00001",
			company=kwargs.get("company"),
			party="Test Customer",
			party_type="Customer",
			payment_type=kwargs.get("payment_type") or "Receive",
			docstatus=kwargs.get("docstatus", 1),
			mode_of_payment="Cash",
			paid_from_account_currency="UGX",
			paid_to="Cash - TC",
			paid_amount=kwargs.get("paid_amount") or 130000,
			reference_no="CASH-001",
			reference_date="2026-11-09",
			check_bank=None,
			custom_receipt=kwargs.get("custom_receipt"),
			references=kwargs.get("references", []),
		)

	def test_fetch_payment_row_details_uses_pe_reference_snapshot(self):
		doc = self._receipt()
		doc.append(
			"receipt_payments",
			{
				"payment_entry": "PE-2026-00001",
				"sales_invoice": "ACC-SINV-2026-00001",
				"amount_received": 0,
			},
		)

		def get_value(doctype, filters=None, fieldname=None, **kwargs):
			if doctype == "Sales Invoice":
				return "2026-11-01"
			if doctype == "Payment Entry Reference":
				return frappe._dict(outstanding_amount=100000, allocated_amount=30000)
			if doctype == "Payment Entry":
				if fieldname == "mode_of_payment":
					return "Cash"
				if fieldname == "paid_to":
					return "Cash - TC"
				if isinstance(fieldname, (list, tuple)):
					return ("CASH-001", "2026-11-09", None)
			return None

		with patch("frappe.db.get_value", side_effect=get_value):
			doc._fetch_payment_row_details()

		row = doc.receipt_payments[0]
		self.assertEqual(row.invoice_date, "2026-11-01")
		self.assertEqual(row.amount_due, 130000)
		self.assertEqual(row.amount_received, 30000)
		self.assertEqual(row.balance_due, 100000)
		self.assertEqual(row.payment_method, "Cash")
		self.assertEqual(row.receiving_account, "Cash - TC")
		self.assertEqual(row.reference_no, "CASH-001")

	def test_compute_totals_and_customer_outstanding(self):
		doc = self._receipt(
			payments=[
				{"sales_invoice": "ACC-SINV-2026-00001", "amount_due": 130000, "amount_received": 30000, "balance_due": 100000},
				{"sales_invoice": None, "amount_due": 0, "amount_received": 50000, "balance_due": 0},
			]
		)

		doc._compute_totals()
		doc._compute_amount_in_words()
		with patch("frappe.db.sql", return_value=[(250000.0,)]):
			doc._compute_customer_outstanding()

		self.assertEqual(doc.total_amount_due, 130000)
		self.assertEqual(doc.total_amount_received, 80000)
		self.assertEqual(doc.total_balance_due, 100000)
		self.assertEqual(doc.customer_total_outstanding, 250000)
		self.assertIn(doc.currency, doc.amount_in_words)

	def test_sync_payment_methods_groups_by_method_reference_and_bank(self):
		doc = self._receipt(
			payments=[
				{"payment_method": "Cash", "amount_received": 10000},
				{"payment_method": "Cash", "amount_received": 5000},
				{
					"payment_method": "Bank",
					"reference_no": "CHQ-001",
					"check_bank": "Test Bank",
					"reference_date": "2026-11-09",
					"amount_received": 20000,
				},
				{
					"payment_method": "Bank",
					"reference_no": "CHQ-001",
					"check_bank": "Test Bank",
					"reference_date": "2026-11-09",
					"amount_received": 5000,
				},
			]
		)

		doc._sync_payment_methods()

		self.assertEqual(len(doc.receipt_payment_methods), 2)
		cash = next(row for row in doc.receipt_payment_methods if row.payment_method == "Cash")
		bank = next(row for row in doc.receipt_payment_methods if row.payment_method == "Bank")
		self.assertEqual(cash.amount, 15000)
		self.assertEqual(bank.amount, 25000)
		self.assertEqual(bank.check_bank, "Test Bank")
		self.assertEqual(bank.reference_no, "CHQ-001")

	def test_duplicate_rows_are_rejected(self):
		doc = self._receipt()
		for _ in range(2):
			doc.append(
				"receipt_payments",
				{"payment_entry": "PE-2026-00001", "sales_invoice": "ACC-SINV-2026-00001"},
			)

		with self.assertRaisesRegex(frappe.ValidationError, "appears more than once"):
			doc._validate_no_duplicates()

	def test_submitted_receipt_duplicate_is_rejected(self):
		doc = self._receipt()
		doc.append(
			"receipt_payments",
			{"payment_entry": "PE-2026-00001", "sales_invoice": "ACC-SINV-2026-00001"},
		)

		with patch("frappe.db.get_value", return_value="RCPT-2026-00009"):
			with self.assertRaisesRegex(frappe.ValidationError, "already covered"):
				doc._validate_no_duplicates()

	def test_get_payment_entry_details_returns_snapshot_row(self):
		pe = self._payment_entry(
			references=[
				frappe._dict(
					reference_doctype="Sales Invoice",
					reference_name="ACC-SINV-2026-00001",
					outstanding_amount=100000,
					allocated_amount=30000,
				)
			]
		)

		with patch("frappe.get_doc", return_value=pe), patch(
			"frappe.db.get_value", return_value="2026-11-01"
		):
			details = get_payment_entry_details(pe.name)

		self.assertEqual(len(details["rows"]), 1)
		row = details["rows"][0]
		self.assertEqual(row["sales_invoice"], "ACC-SINV-2026-00001")
		self.assertEqual(row["amount_due"], 130000)
		self.assertEqual(row["amount_received"], 30000)
		self.assertEqual(row["balance_due"], 100000)
		self.assertEqual(row["payment_method"], "Cash")

	def test_get_payment_entry_details_rejects_draft(self):
		pe = self._payment_entry(docstatus=0)

		with patch("frappe.get_doc", return_value=pe):
			with self.assertRaisesRegex(frappe.ValidationError, "must be submitted"):
				get_payment_entry_details(pe.name)

	def test_get_payment_entry_details_returns_advance_row(self):
		pe = self._payment_entry(references=[])

		with patch("frappe.get_doc", return_value=pe):
			details = get_payment_entry_details(pe.name)

		self.assertEqual(len(details["rows"]), 1)
		row = details["rows"][0]
		self.assertIsNone(row["sales_invoice"])
		self.assertEqual(row["amount_received"], 130000)
		self.assertEqual(row["balance_due"], 0)

	def test_create_receipt_from_pe_prefills_rows(self):
		pe = self._payment_entry(company="Test Company")
		details = {
			"rows": [
				{
					"payment_entry": pe.name,
					"sales_invoice": "ACC-SINV-2026-00001",
					"invoice_date": "2026-11-01",
					"amount_due": 130000,
					"amount_received": 30000,
					"balance_due": 100000,
					"payment_method": "Cash",
					"receiving_account": "Cash - TC",
					"reference_no": "CASH-001",
					"reference_date": "2026-11-09",
					"check_bank": None,
				}
			],
			"mode_of_payment": "Cash",
			"paid_to": "Cash - TC",
		}

		original_get_doc = frappe.get_doc

		def get_doc(*args, **kwargs):
			if args and args[0] == "Payment Entry":
				return pe
			return original_get_doc(*args, **kwargs)

		with patch("frappe.get_doc", side_effect=get_doc), patch(
			"subamaz.subamaz.doctype.receipt.receipt._set_customer_addresses"
		), patch(
			"subamaz.subamaz.doctype.receipt.receipt.get_payment_entry_details",
			return_value=details,
		):
			receipt = create_receipt_from_pe(pe.name)

		self.assertEqual(receipt.company, "Test Company")
		self.assertEqual(receipt.customer, "Test Customer")
		self.assertEqual(len(receipt.receipt_payments), 1)
		self.assertEqual(receipt.receipt_payments[0].sales_invoice, "ACC-SINV-2026-00001")

	def test_create_receipt_from_pe_rejects_existing_receipt(self):
		pe = self._payment_entry(custom_receipt="RCPT-2026-00001")

		with patch("frappe.get_doc", return_value=pe):
			with self.assertRaisesRegex(frappe.ValidationError, "already exists"):
				create_receipt_from_pe(pe.name)

	def test_submit_and_cancel_update_payment_entries(self):
		doc = self._receipt(
			payments=[
				{"payment_entry": "PE-2026-00001"},
				{"payment_entry": "PE-2026-00002"},
				{"payment_entry": "PE-2026-00001"},
			]
		)
		doc.name = "RCPT-2026-00001"

		with patch("frappe.db.set_value") as set_value:
			doc._update_payment_entries("submit")

		self.assertEqual(set_value.call_count, 2)
		updated = {call.args[1] for call in set_value.call_args_list}
		self.assertEqual(updated, {"PE-2026-00001", "PE-2026-00002"})
		for call in set_value.call_args_list:
			self.assertEqual(call.args[3], "RCPT-2026-00001")

		with patch("frappe.db.set_value") as set_value:
			doc._update_payment_entries("cancel")

		for call in set_value.call_args_list:
			self.assertIsNone(call.args[3])
