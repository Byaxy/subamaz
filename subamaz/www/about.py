import frappe

from subamaz.api.branding import get_garage_abbr


def get_context(context):
	branding = frappe.get_single("Garage Branding Settings")
	context.branding = branding
	context.abbr = get_garage_abbr()
	return context
