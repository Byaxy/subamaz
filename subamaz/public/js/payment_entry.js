// Copyright (c) 2026, SubaMaz Contributors
// See license.txt

function maybe_add_receipt_button(frm) {
	if (
		frm.doc.docstatus !== 1 ||
		frm.doc.payment_type !== "Receive" ||
		frm.doc.party_type !== "Customer"
	)
		return;

	if (frm.doc.custom_receipt) {
		frm.add_custom_button(
			__("Receipt"),
			() => frappe.set_route("Form", "Receipt", frm.doc.custom_receipt),
			__("View")
		);
	} else {
		frm.add_custom_button(
			__("Receipt"),
			() =>
				frappe.model.open_mapped_doc({
					method: "subamaz.subamaz.doctype.receipt.receipt.create_receipt_from_pe",
					frm: frm,
				}),
			__("Create")
		);
		frm.page.set_inner_btn_group_as_primary(__("Create"));
	}
}

frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		maybe_add_receipt_button(frm);
	},
});
