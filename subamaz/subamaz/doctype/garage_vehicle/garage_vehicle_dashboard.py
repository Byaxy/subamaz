import frappe

TRANSACTIONS = [
	{
		"label": "Service Flow",
		"items": ["Vehicle Reception", "Vehicle Inspection", "Service Order", "Vehicle Delivery"],
	}
]


def get_data():
	# guard for phases not yet built: only surface doctypes that exist
	transactions = [
		{**group, "items": [dt for dt in group["items"] if frappe.db.exists("DocType", dt)]}
		for group in TRANSACTIONS
	]
	return {
		"fieldname": "vehicle",
		"transactions": [group for group in transactions if group["items"]],
	}
