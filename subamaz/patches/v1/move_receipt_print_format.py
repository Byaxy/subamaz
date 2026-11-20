import frappe

from subamaz.patches.v1.set_subamaz_print_format_defaults import _set_default

PRINT_FORMAT = "SubaMaz Payment Receipt"


def execute():
	if frappe.db.exists("Print Format", PRINT_FORMAT):
		print_format = frappe.get_doc("Print Format", PRINT_FORMAT)
		if print_format.doc_type != "Receipt":
			print_format.doc_type = "Receipt"
			print_format.save(ignore_permissions=True)

	_remove_payment_entry_default()

	if frappe.db.exists("Print Format", PRINT_FORMAT):
		_set_default("Receipt", PRINT_FORMAT)

	frappe.clear_cache(doctype="Payment Entry")
	frappe.clear_cache(doctype="Receipt")


def _remove_payment_entry_default():
	for row in frappe.get_all(
		"Property Setter",
		filters={
			"doc_type": "Payment Entry",
			"property": "default_print_format",
			"doctype_or_field": "DocType",
		},
		fields=["name", "value"],
	):
		if row.value == PRINT_FORMAT:
			frappe.delete_doc("Property Setter", row.name, ignore_permissions=True, force=True)
