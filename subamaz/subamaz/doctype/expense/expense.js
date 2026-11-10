// Copyright (c) 2026, SubaMaz Contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense", {
	setup(frm) {
		frm.set_query("mode_of_payment", () => ({ filters: { enabled: 1 } }));
		frm.set_query("cost_center", () => ({
			filters: {
				company: frm.doc.company || frappe.defaults.get_user_default("Company"),
				is_group: 0,
			},
		}));
		frm.set_query("purchase_invoice", () => ({
			query: "subamaz.subamaz.doctype.expense.queries.get_purchase_invoices_search",
			filters: {
				company: frm.doc.company || frappe.defaults.get_user_default("Company"),
			},
		}));
		frm.set_query("purchase_order", "purchase_orders", () => ({
			query: "subamaz.subamaz.doctype.expense.queries.get_purchase_orders_search",
			filters: {
				company: frm.doc.company || frappe.defaults.get_user_default("Company"),
			},
		}));
		frm.set_query("expense_category", () => {
			if (!frm.doc.is_accompanying) return {};
			return { filters: { is_accompanying_expense: 1 } };
		});
	},

	refresh(frm) {
		frm.set_df_property("paid_from", "read_only", 1);
		toggle_fields(frm);
		resolve_paid_to(frm);
		toggle_action_buttons(frm);
	},

	company(frm) {
		frm.set_value("cost_center", null);
		frm.set_value("purchase_invoice", null);
		frm.set_value("mode_of_payment", null);
		frm.set_value("paid_from", null);
		frm.set_value("paid_from_account_currency", null);
		frm.set_value("paid_to", null);
		frm.set_value("paid_to_account_currency", null);
		frm.clear_table("purchase_orders");
		frm.refresh_field("purchase_orders");
	},

	payment_type(frm) {
		if (frm.doc.payment_type === "Direct Payment") {
			frm.set_value("purchase_invoice", null);
		}
		toggle_fields(frm);
		resolve_paid_to(frm);
	},

	mode_of_payment(frm) {
		if (!frm.doc.mode_of_payment) {
			frm.set_value("paid_from", null);
			frm.set_value("paid_from_account_currency", null);
			return;
		}
		frappe.call({
			method: "subamaz.subamaz.doctype.expense.queries.get_payment_method_account",
			args: {
				mode_of_payment: frm.doc.mode_of_payment,
				company: frm.doc.company || frappe.defaults.get_user_default("Company"),
			},
			callback(r) {
				if (!r.message) return;
				frm.set_value("paid_from", r.message.account);
				frm.set_value("paid_from_account_currency", r.message.account_currency);
			},
		});
	},

	expense_category(frm) {
		resolve_paid_to(frm);
	},

	is_accompanying(frm) {
		if (!frm.doc.is_accompanying) {
			frm.clear_table("purchase_orders");
			frm.refresh_field("purchase_orders");
		}
		toggle_fields(frm);
		resolve_paid_to(frm);
	},

	purchase_invoice(frm) {
		if (!frm.doc.purchase_invoice) {
			resolve_paid_to(frm);
			return;
		}
		frappe.call({
			method: "subamaz.subamaz.doctype.expense.queries.get_invoice_details",
			args: { purchase_invoice: frm.doc.purchase_invoice },
			callback(r) {
				if (!r.message) return;
				const pi = r.message;
				frm.set_value("amount", pi.outstanding_amount);
				if (!frm.doc.payee) {
					frm.set_value("payee", pi.supplier_name || pi.supplier);
				}
				resolve_paid_to(frm);
				frappe.show_alert(
					{
						message: __("Outstanding: {0}", [
							frappe.format(pi.outstanding_amount, { fieldtype: "Currency" }),
						]),
						indicator: "blue",
					},
					5
				);
			},
		});
	},
});

frappe.ui.form.on("Expense Purchase Order", {
	purchase_order(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.purchase_order || !frm.doc.company) return;

		const duplicate = (frm.doc.purchase_orders || []).some(
			(other) => other.name !== cdn && other.purchase_order === row.purchase_order
		);
		if (duplicate) {
			frappe.msgprint(__("Purchase Order {0} already added.", [row.purchase_order]));
			frappe.model.set_value(cdt, cdn, "purchase_order", "");
			return;
		}

		frappe.db.get_value("Purchase Order", row.purchase_order, "company", (r) => {
			if (r && r.company !== frm.doc.company) {
				frappe.msgprint(__("The selected Purchase Order belongs to a different company."));
				frappe.model.set_value(cdt, cdn, "purchase_order", "");
			}
		});
	},
});

function toggle_fields(frm) {
	const is_invoice = frm.doc.payment_type === "Against Purchase Invoice";
	frm.set_df_property("purchase_invoice", "hidden", is_invoice ? 0 : 1);
	frm.set_df_property("purchase_invoice", "reqd", is_invoice ? 1 : 0);

	const needs_category = frm.doc.payment_type === "Direct Payment" || frm.doc.is_accompanying;
	frm.set_df_property("expense_category", "reqd", needs_category ? 1 : 0);

	frm.set_df_property("purchase_orders", "hidden", frm.doc.is_accompanying ? 0 : 1);
	frm.set_df_property("purchase_orders", "reqd", frm.doc.is_accompanying ? 1 : 0);
	frm.refresh_fields(["purchase_invoice", "expense_category", "purchase_orders"]);
}

function resolve_paid_to(frm) {
	if (frm.doc.payment_type === "Against Purchase Invoice") {
		if (!frm.doc.purchase_invoice) {
			set_paid_to(frm, null, null);
			return;
		}
		frappe.db.get_value("Purchase Invoice", frm.doc.purchase_invoice, "supplier", (r) => {
			if (!r || !r.supplier) return;
			frappe.call({
				method: "subamaz.subamaz.doctype.expense.queries.get_supplier_payable_details",
				args: {
					supplier: r.supplier,
					company: frm.doc.company || frappe.defaults.get_user_default("Company"),
				},
				callback(res) {
					if (!res.message) return;
					set_paid_to(frm, res.message.paid_to, res.message.account_currency);
				},
			});
		});
		return;
	}

	if (!frm.doc.expense_category) {
		set_paid_to(frm, null, null);
		return;
	}
	frappe.db.get_value("Expense Category", frm.doc.expense_category, "expense_account", (r) => {
		if (!r || !r.expense_account) {
			set_paid_to(frm, null, null);
			return;
		}
		frappe.db.get_value("Account", r.expense_account, "account_currency", (cr) => {
			set_paid_to(frm, r.expense_account, cr ? cr.account_currency : null);
		});
	});
}

function set_paid_to(frm, account, currency) {
	frm.set_value("paid_to", account);
	frm.set_value("paid_to_account_currency", currency);
}

function purchase_order_names(frm) {
	return (frm.doc.purchase_orders || []).map((row) => row.purchase_order).filter(Boolean);
}

function toggle_action_buttons(frm) {
	const actions = [
		["Landed Cost Voucher", "Create"],
		["View Landed Cost Voucher", "View"],
		["View Payment Entry", "View"],
		["View Journal Entry", "View"],
	];
	actions.forEach(([label, group]) => frm.remove_custom_button(__(label), __(group)));
	purchase_order_names(frm).forEach((po) =>
		frm.remove_custom_button(__(`View PO: ${po}`), __("View"))
	);

	if (frm.doc.docstatus === 1 && frm.doc.is_accompanying && !frm.doc.landed_cost_voucher) {
		if (purchase_order_names(frm).length) {
			frm.add_custom_button(
				__("Landed Cost Voucher"),
				() => create_landed_cost_voucher(frm),
				__("Create")
			);
		}
	}

	if (frm.doc.landed_cost_voucher) {
		frm.add_custom_button(
			__("View Landed Cost Voucher"),
			() => frappe.set_route("Form", "Landed Cost Voucher", frm.doc.landed_cost_voucher),
			__("View")
		);
	}
	if (frm.doc.payment_entry) {
		frm.add_custom_button(
			__("View Payment Entry"),
			() => frappe.set_route("Form", "Payment Entry", frm.doc.payment_entry),
			__("View")
		);
	}
	if (frm.doc.journal_entry) {
		frm.add_custom_button(
			__("View Journal Entry"),
			() => frappe.set_route("Form", "Journal Entry", frm.doc.journal_entry),
			__("View")
		);
	}
	purchase_order_names(frm).forEach((po) => {
		frm.add_custom_button(
			__(`View PO: ${po}`),
			() => frappe.set_route("Form", "Purchase Order", po),
			__("View")
		);
	});
}

function create_landed_cost_voucher(frm) {
	const po_names = purchase_order_names(frm);
	frappe.call({
		method: "subamaz.subamaz.doctype.expense.landed_cost.check_purchase_orders_fully_received",
		args: { po_names },
		freeze: true,
		freeze_message: __("Checking receiving status..."),
		callback(r) {
			if (!r.message) return;
			if (!r.message.ready) {
				frappe.msgprint({
					title: __("Purchase Orders Not Fully Received"),
					message: r.message.message,
					indicator: "red",
				});
				return;
			}
			frappe.confirm(
				__(
					"Create a new Landed Cost Voucher for <b>{0}</b>?<br><br>" +
						"Review the document, click <b>Get Items</b>, distribute the charges, then submit."
				).replace("{0}", frm.doc.name),
				() =>
					frappe.model.open_mapped_doc({
						method: "subamaz.subamaz.doctype.expense.landed_cost.make_landed_cost_voucher",
						frm,
					})
			);
		},
	});
}
