from frappe import _


def get_data():
	return {
		"fieldname": "job_card",
		"transactions": [
			{"label": _("Repair Tasks"), "items": ["Repair Task"]},
			{"label": _("Stock"), "items": ["Stock Entry"]},
		],
	}
