import frappe

BRANDING = "Garage Branding Settings"

VALUES = {
	"garage_name": ("SubaMaz Auto", ("SubaMaz",)),
	"address": (
		"Plot 190 Namuli Road, Behind Kabira Country Club, Kampala, Uganda",
		("Plot 12, Lumumba Avenue, Kampala, Uganda",),
	),
	"phone": ("0703 691 580 (WhatsApp) | 0787 178 113 (Call)", ("+256 700 123456",)),
	"email": ("subamaz125@gmail.com", ("info@subamaz.ug",)),
	"logo": ("/assets/subamaz/images/print/subamaz-logo-navy.png", ()),
}


def execute():
	for fieldname, (value, old_values) in VALUES.items():
		current = frappe.db.get_single_value(BRANDING, fieldname)
		if current not in (None, "", *old_values):
			continue
		frappe.db.set_single_value(BRANDING, fieldname, value)

	frappe.clear_cache(doctype=BRANDING)
