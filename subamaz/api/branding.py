import frappe


def get_garage_abbr() -> str:
	"""Return the garage's display abbreviation for the text logo mark.

	Prefers the ERPNext Company abbreviation when the default company is named
	exactly like the garage (e.g. Company "SubaMaz" -> "SM"). Otherwise the
	abbreviation is derived from the garage name the same way Frappe does,
	first letters of each word ("SubaMaz Garage" -> "SG").
	"""
	garage_name = (frappe.get_single("Garage Branding Settings").garage_name or "").strip()
	company = frappe.defaults.get_defaults().get("company")
	if company and frappe.db.exists("Company", company):
		doc = frappe.get_cached_doc("Company", company)
		if doc.abbr and doc.name == garage_name:
			return doc.abbr
	return frappe.utils.get_abbr(garage_name or "GM", max_len=2)
