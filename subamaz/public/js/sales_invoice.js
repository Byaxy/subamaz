// Copyright (c) 2026, SubaMaz Contributors
// For license information, please see license.txt

frappe.ui.form.on("Sales Invoice", {
	setup(frm) {
		// Only vehicles belonging to the selected customer are selectable.
		frm.set_query("garage_vehicle", () => {
			if (!frm.doc.customer) return {};
			return { filters: { customer: frm.doc.customer } };
		});
	},

	customer(frm) {
		// Clear a vehicle that belongs to a different customer.
		if (!frm.doc.garage_vehicle) return;
		if (!frm.doc.customer) {
			frm.set_value("garage_vehicle", null);
			return;
		}
		frappe.db
			.get_value("Garage Vehicle", frm.doc.garage_vehicle, "customer")
			.then((r) => {
				if (r.message && r.message.customer !== frm.doc.customer)
					frm.set_value("garage_vehicle", null);
			});
	},
});
