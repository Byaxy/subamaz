import frappe

LEGACY_FORMATS = ("Garage Invoice", "Garage Quotation", "Job Sheet")


def execute():
	for name in LEGACY_FORMATS:
		if frappe.db.exists("Print Format", name):
			frappe.delete_doc("Print Format", name, ignore_missing=True, force=True)
	frappe.clear_cache()
