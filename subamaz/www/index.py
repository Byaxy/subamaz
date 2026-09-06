import frappe

from subamaz.api.branding import get_garage_abbr


def get_context(context):
	branding = frappe.get_single("Garage Branding Settings")
	context.branding = branding
	context.abbr = get_garage_abbr()

	# services catalog: Repair templates
	try:
		context.services = frappe.get_all(
			"Service Checklist Template",
			filters={"applies_to": "Repair"},
			fields=["template_name"],
			order_by="modified asc",
			limit=6,
		)
	except Exception:
		context.services = []

	# recent blog posts
	try:
		context.blogs = frappe.get_all(
			"Blog Post",
			filters={"published": 1},
			fields=["name", "title", "route", "published_on", "blogger", "blog_intro"],
			order_by="published_on desc",
			limit=3,
		)
	except Exception:
		context.blogs = []

	context.parents = [{"name": "home", "title": "Home", "route": "/"}]
	return context
