import frappe

from subamaz.api import DEFAULTS


def execute():
	theme = frappe.get_doc("Theme")
	for fieldname, value in DEFAULTS.items():
		theme.set(fieldname, value)
	theme.flags.ignore_permissions = True
	theme.save()
