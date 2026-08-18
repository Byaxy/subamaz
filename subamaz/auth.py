import frappe


def enforce_app_lockout():
	user = frappe.session.user
	if user == "Guest":
		return
	if not frappe.request.path.startswith("/app"):
		return
	if "System Manager" in frappe.get_roles(user):
		return
	is_website_user = frappe.db.get_value("User", user, "user_type") == "Website User"
	frappe.local.flags.redirect_location = "/portal" if is_website_user else "/garage"
	raise frappe.Redirect
