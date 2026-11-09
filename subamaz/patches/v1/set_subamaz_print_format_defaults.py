import frappe

DEFAULTS = {
	"Sales Invoice": "SubaMaz Sales Invoice",
	"Payment Entry": "SubaMaz Payment Receipt",
	"Quotation": "SubaMaz Pro-Forma Invoice",
	"Purchase Order": "SubaMaz Purchase Order",
	"Request for Quotation": "SubaMaz Request for Quotation",
}


def execute():
	for doctype, new_format in DEFAULTS.items():
		if not frappe.db.exists("Print Format", new_format):
			continue
		_set_default(doctype, new_format)


def _set_default(doctype, value):
	rows = frappe.get_all(
		"Property Setter",
		filters={
			"doc_type": doctype,
			"property": "default_print_format",
			"doctype_or_field": "DocType",
		},
		fields=["name"],
		limit=1,
	)
	if rows:
		frappe.db.set_value(
			"Property Setter",
			rows[0].name,
			"value",
			value,
			update_modified=False,
		)
	else:
		frappe.make_property_setter(
			{
				"doctype": doctype,
				"doctype_or_field": "DocType",
				"property": "default_print_format",
				"value": value,
				"property_type": "Data",
			},
			module="Subamaz",
		)
	frappe.clear_cache(doctype=doctype)
