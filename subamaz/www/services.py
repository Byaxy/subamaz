import frappe

from subamaz.api.branding import get_garage_abbr


def get_context(context):
	branding = frappe.get_single("Garage Branding Settings")
	context.branding = branding
	context.abbr = get_garage_abbr()
	try:
		context.services = frappe.get_all(
			"Service Checklist Template",
			filters={"applies_to": "Repair"},
			fields=["template_name"],
			order_by="modified asc",
		)
	except Exception:
		context.services = []
	# include item breakdown for each template (optional)
	for s in context.services:
		try:
			tmpl = frappe.get_doc("Service Checklist Template", s.template_name)
			s["items"] = [row.item_description for row in tmpl.items[:6]]
		except Exception:
			s["items"] = []
	return context
