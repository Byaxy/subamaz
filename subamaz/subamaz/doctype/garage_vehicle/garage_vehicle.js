// Copyright (c) 2026, SubaMaz Contributors
// For license information, please see license.txt

frappe.ui.form.on("Garage Vehicle", {
	setup(frm) {
		// Only models belonging to the selected make are selectable.
		frm.set_query("model", () => {
			if (!frm.doc.make) return {};
			return { filters: { make: frm.doc.make } };
		});
	},

	make(frm) {
		// Clear a model that belongs to a different make.
		if (!frm.doc.model) return;
		if (!frm.doc.make) {
			frm.set_value("model", null);
			return;
		}
		frappe.db.get_value("Vehicle Model", frm.doc.model, "make").then((r) => {
			if (r.message && r.message.make !== frm.doc.make) frm.set_value("model", null);
		});
	},
});
