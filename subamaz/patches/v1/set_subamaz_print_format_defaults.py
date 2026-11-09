import frappe

DEFAULTS = {
	"Sales Invoice": ("SubaMaz Sales Invoice", ("Garage Invoice",)),
	"Payment Entry": ("SubaMaz Payment Receipt", ("Payment Receipt", "Payment Entry")),
}


def execute():
	for doctype, (new_format, old_formats) in DEFAULTS.items():
		if not frappe.db.exists("Print Format", new_format):
			continue

		current = _current_default(doctype)
		if current not in (None, "", new_format, *old_formats):
			continue
		if current != new_format:
			_set_default(doctype, new_format)


def _current_default(doctype):
	rows = frappe.get_all(
		"Property Setter",
		filters={
			"doc_type": doctype,
			"property": "default_print_format",
			"doctype_or_field": "DocType",
		},
		fields=["name", "value"],
		limit=1,
	)
	return rows[0].value if rows else None


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
