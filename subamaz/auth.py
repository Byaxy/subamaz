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


def get_website_user_home_page(user):
	"""Keep System Managers on Desk; Website Users with a linked Customer go to portal."""
	if "System Manager" in frappe.get_roles(user):
		return "desk"
	# Portal detection: Website User linked to Contact → Customer
	try:
		if frappe.db.get_value("User", user, "user_type") == "Website User":
			# Find Contact linked to this user
			contact = frappe.db.get_value("Contact", {"user": user}, "name")
			if not contact:
				email = frappe.db.get_value("User", user, "email")
				if email:
					contact = frappe.db.get_value("Contact", {"email_id": email}, "name")
					if not contact:
						# Check Contact Email child table
						contact = frappe.db.get_value("Contact Email", {"email_id": email}, "parent")
			if contact:
				customer = frappe.db.get_value(
					"Dynamic Link", {"parent": contact, "parenttype": "Contact", "link_doctype": "Customer"}, "link_name"
				)
				if customer:
					return "portal"
				# Fallback: any Customer linked?
				if frappe.db.exists("Contact", contact):
					return "portal"
	except Exception:
		pass
	return None
