// Copyright (c) 2026, SubaMaz Contributors
// For license information, please see license.txt

frappe.listview_settings["Expense"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Add Multiple Expenses"), () =>
			open_bulk_expense_dialog(listview)
		);
	},
};

function open_bulk_expense_dialog(listview) {
	frappe.db
		.get_list("Expense Category", {
			fields: ["name", "is_accompanying_expense"],
			limit: 500,
		})
		.then((categories) => {
			const dialog = new frappe.ui.Dialog({
				title: __("Add Multiple Expenses"),
				size: "extra-large",
				fields: [
					{ fieldtype: "HTML", fieldname: "rows_html" },
					{ fieldtype: "Section Break" },
					{ fieldtype: "HTML", fieldname: "summary_html" },
				],
				primary_action_label: __("Submit All"),
				primary_action() {
					submit_all(dialog, listview);
				},
			});
			dialog._rows = [];
			dialog._categories = new Map(
				(categories || []).map((row) => [row.name, row.is_accompanying_expense])
			);
			dialog.show();
			render_rows(dialog);
		});
}

function render_rows(dialog) {
	const rows = dialog._rows;
	const total = rows.reduce((sum, row) => sum + flt(row.amount), 0);
	dialog.fields_dict.rows_html.$wrapper.html(`
		<div class="d-flex justify-content-between align-items-center mb-3">
			<div>
				<b>${__("Expenses")}</b>
				<div class="text-muted small">${__("Add rows, review, then submit all.")}</div>
			</div>
			<button class="btn btn-default btn-sm bulk-add-row">+ ${__("Add Row")}</button>
		</div>
		<div class="table-responsive">
			<table class="table table-bordered table-sm">
				<thead>
					<tr>
						<th>#</th>
						<th>${__("Date")}</th>
						<th>${__("Description")}</th>
						<th>${__("Category")}</th>
						<th>${__("Payee")}</th>
						<th>${__("Payment Method")}</th>
						<th>${__("Type")}</th>
						<th class="text-right">${__("Amount")}</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					${
						rows.length
							? rows.map((row, index) => row_html(row, index)).join("")
							: `<tr><td colspan="9" class="text-center text-muted py-4">${__(
									"No expenses added yet."
							  )}</td></tr>`
					}
				</tbody>
			</table>
		</div>
	`);

	dialog.fields_dict.rows_html.$wrapper.find(".bulk-add-row").on("click", () => open_row_dialog(dialog));
	dialog.fields_dict.rows_html.$wrapper.find(".bulk-edit").on("click", function () {
		open_row_dialog(dialog, Number($(this).data("idx")));
	});
	dialog.fields_dict.rows_html.$wrapper.find(".bulk-delete").on("click", function () {
		const index = Number($(this).data("idx"));
		dialog._rows.splice(index, 1);
		render_rows(dialog);
	});

	dialog.fields_dict.summary_html.$wrapper.html(`
		<div class="d-flex justify-content-between align-items-center">
			<span><b>${rows.length}</b> ${__("expense(s)")}</span>
			<span>${__("Total")}: <b>${frappe.format(total, { fieldtype: "Currency" })}</b></span>
		</div>
	`);
	dialog.get_primary_btn().prop("disabled", !rows.length);
}

function row_html(row, index) {
	return `
		<tr>
			<td>${index + 1}</td>
			<td>${frappe.datetime.str_to_user(row.expense_date)}</td>
			<td>${esc(row.expense_description)}</td>
			<td>${esc(row.expense_category || "—")}</td>
			<td>${esc(row.payee)}</td>
			<td>${esc(row.mode_of_payment)}</td>
			<td>${esc(row.payment_type)}</td>
			<td class="text-right">${frappe.format(row.amount, { fieldtype: "Currency" })}</td>
			<td class="text-right">
				<button class="btn btn-xs btn-default bulk-edit" data-idx="${index}">
					<i class="fa fa-pencil"></i>
				</button>
				<button class="btn btn-xs btn-default bulk-delete" data-idx="${index}">
					<i class="fa fa-trash text-danger"></i>
				</button>
			</td>
		</tr>
	`;
}

function open_row_dialog(parent, index) {
	const editing = index !== undefined ? parent._rows[index] : null;
	const dialog = new frappe.ui.Dialog({
		title: editing ? __("Edit Expense") : __("Add Expense"),
		size: "large",
		fields: row_fields(editing),
		primary_action_label: editing ? __("Save") : __("Add"),
		primary_action(values) {
			save_row(parent, dialog, index, values);
		},
	});
	dialog._parent = parent;
	dialog._categories = parent._categories;
	dialog._po_controls = [];
	dialog._resolved_account = editing ? editing.paid_from : null;
	wire_row_dialog(dialog, editing);
	dialog.show();
}

function row_fields(row) {
	const value = (key, fallback = "") => (row && row[key] !== undefined ? row[key] : fallback);
	return [
		{ fieldtype: "Section Break" },
		{
			fieldtype: "Data",
			fieldname: "expense_description",
			label: __("Expense Description"),
			reqd: 1,
			default: value("expense_description"),
		},
		{
			fieldtype: "Currency",
			fieldname: "amount",
			label: __("Paid Amount"),
			reqd: 1,
			default: value("amount", ""),
		},
		{
			fieldtype: "Data",
			fieldname: "payee",
			label: __("Payee"),
			reqd: 1,
			default: value("payee"),
		},
		{ fieldtype: "Column Break" },
		{
			fieldtype: "Date",
			fieldname: "expense_date",
			label: __("Expense Date"),
			reqd: 1,
			default: value("expense_date", frappe.datetime.get_today()),
		},
		{
			fieldtype: "Select",
			fieldname: "payment_type",
			label: __("Payment Type"),
			options: ["Direct Payment", "Against Purchase Invoice"],
			default: value("payment_type", "Direct Payment"),
			reqd: 1,
		},
		{
			fieldtype: "Link",
			fieldname: "mode_of_payment",
			label: __("Payment Method"),
			options: "Mode of Payment",
			reqd: 1,
			get_query: () => ({ filters: { enabled: 1 } }),
			default: value("mode_of_payment"),
		},
		{ fieldtype: "Section Break", label: __("Category & Invoice") },
		{
			fieldtype: "Link",
			fieldname: "expense_category",
			label: __("Expense Category"),
			options: "Expense Category",
			default: value("expense_category"),
		},
		{
			fieldtype: "Link",
			fieldname: "purchase_invoice",
			label: __("Purchase Invoice"),
			options: "Purchase Invoice",
			default: value("purchase_invoice"),
		},
		{ fieldtype: "Section Break", label: __("Payment Reference") },
		{
			fieldtype: "Data",
			fieldname: "reference_no",
			label: __("Payment Reference No"),
			default: value("reference_no"),
		},
		{ fieldtype: "Column Break" },
		{
			fieldtype: "Date",
			fieldname: "reference_date",
			label: __("Payment Reference Date"),
			default: value("reference_date"),
		},
		{ fieldtype: "Section Break", label: __("Accompanying Expense") },
		{
			fieldtype: "Check",
			fieldname: "is_accompanying",
			label: __("Is Accompanying Expense"),
			default: value("is_accompanying", 0),
		},
		{ fieldtype: "HTML", fieldname: "purchase_orders_html" },
		{ fieldtype: "Section Break" },
		{
			fieldtype: "Small Text",
			fieldname: "notes",
			label: __("Notes"),
			default: value("notes"),
		},
	];
}

function wire_row_dialog(dialog, editing) {
	const fields = dialog.fields_dict;
	fields.expense_category.get_query = () =>
		dialog.get_value("is_accompanying") ? { filters: { is_accompanying_expense: 1 } } : {};
	fields.purchase_invoice.get_query = () => ({
		query: "subamaz.subamaz.doctype.expense.queries.get_purchase_invoices_search",
		filters: { company: frappe.defaults.get_user_default("Company") },
	});

	const sync = () => {
		const is_invoice = dialog.get_value("payment_type") === "Against Purchase Invoice";
		const accompanying = Boolean(dialog.get_value("is_accompanying"));
		toggle_field(dialog, "purchase_invoice", is_invoice);
		toggle_field(dialog, "expense_category", !is_invoice || accompanying);
		toggle_field(dialog, "purchase_orders_html", accompanying);
	};
	dialog._sync = sync;

	fields.payment_type.$input.on("change", () => {
		if (dialog.get_value("payment_type") === "Direct Payment") {
			fields.purchase_invoice.set_value("");
		} else if (!dialog.get_value("is_accompanying")) {
			fields.expense_category.set_value("");
		}
		sync();
	});
	fields.is_accompanying.$input.on("change", () => {
		if (!dialog.get_value("is_accompanying")) clear_po_controls(dialog);
		sync();
	});
	fields.purchase_invoice.$input.on("change", () => {
		const invoice = dialog.get_value("purchase_invoice");
		if (!invoice) return;
		frappe.call({
			method: "subamaz.subamaz.doctype.expense.queries.get_invoice_details",
			args: { purchase_invoice: invoice },
			callback(r) {
				if (!r.message) return;
				fields.amount.set_value(r.message.outstanding_amount);
				if (!dialog.get_value("payee")) {
					fields.payee.set_value(r.message.supplier_name || r.message.supplier);
				}
			},
		});
	});
	fields.mode_of_payment.$input.on("change", () => {
		const mode = dialog.get_value("mode_of_payment");
		dialog._resolved_account = null;
		if (!mode) return;
		frappe.call({
			method: "subamaz.subamaz.doctype.expense.queries.get_payment_method_account",
			args: { mode_of_payment: mode, company: frappe.defaults.get_user_default("Company") },
			callback(r) {
				if (dialog.get_value("mode_of_payment") !== mode || !r.message) return;
				dialog._resolved_account = r.message.account;
			},
		});
	});

	build_po_container(dialog);
	((editing && editing.purchase_orders) || []).forEach((row) =>
		add_po_control(dialog, row.purchase_order)
	);
	sync();
}

function save_row(parent, dialog, index, values) {
	const errors = validate_row(dialog, values);
	if (errors.length) {
		frappe.msgprint(errors.join("<br>"));
		return;
	}
	resolve_account(dialog, values.mode_of_payment, () => {
		const row = {
			expense_description: values.expense_description,
			amount: flt(values.amount),
			payee: values.payee,
			expense_date: values.expense_date,
			payment_type: values.payment_type,
			mode_of_payment: values.mode_of_payment,
			paid_from: dialog._resolved_account,
			expense_category: values.expense_category || null,
			purchase_invoice: values.purchase_invoice || null,
			reference_no: values.reference_no || null,
			reference_date: values.reference_date || null,
			is_accompanying: values.is_accompanying ? 1 : 0,
			purchase_orders: po_names(dialog).map((name) => ({ purchase_order: name })),
			notes: values.notes || null,
		};
		if (index !== undefined) parent._rows[index] = row;
		else parent._rows.push(row);
		dialog.hide();
		render_rows(parent);
	});
}

function validate_row(dialog, values) {
	const errors = [];
	["expense_description", "payee", "expense_date", "mode_of_payment"].forEach((field) => {
		if (!values[field]) errors.push(__("{0} is required", [dialog.fields_dict[field].df.label]));
	});
	if (!(flt(values.amount) > 0)) errors.push(__("Enter an amount above zero"));
	const is_invoice = values.payment_type === "Against Purchase Invoice";
	const accompanying = Boolean(values.is_accompanying);
	if ((!is_invoice || accompanying) && !values.expense_category) {
		errors.push(__("Expense Category is required"));
	}
	if (is_invoice && !values.purchase_invoice) errors.push(__("Purchase Invoice is required"));
	if (accompanying && !po_names(dialog).length) {
		errors.push(__("Add at least one Purchase Order"));
	}
	const names = po_names(dialog);
	if (names.length !== new Set(names).size) {
		errors.push(__("Duplicate Purchase Order found"));
	}
	if (accompanying && values.expense_category && dialog._categories) {
		const flagged = Boolean(dialog._categories.get(values.expense_category));
		if (!flagged) errors.push(__("Use a category marked as an Accompanying Expense Category"));
	}
	return errors;
}

function resolve_account(dialog, mode, callback) {
	if (dialog._resolved_account || !mode) {
		callback();
		return;
	}
	frappe.call({
		method: "subamaz.subamaz.doctype.expense.queries.get_payment_method_account",
		args: { mode_of_payment: mode, company: frappe.defaults.get_user_default("Company") },
		callback(r) {
			dialog._resolved_account = r.message ? r.message.account : null;
			callback();
		},
	});
}

function build_po_container(dialog) {
	const wrapper = dialog.fields_dict.purchase_orders_html.$wrapper;
	wrapper.html(`
		<div class="bulk-po-section">
			<label class="control-label">${__("Purchase Orders")}</label>
			<div class="bulk-po-list"></div>
			<button class="btn btn-xs btn-default bulk-po-add">+ ${__("Purchase Order")}</button>
		</div>
	`);
	wrapper.find(".bulk-po-add").on("click", () => add_po_control(dialog, ""));
}

function add_po_control(dialog, value) {
	const company = frappe.defaults.get_user_default("Company");
	const list = dialog.fields_dict.purchase_orders_html.$wrapper.find(".bulk-po-list");
	const wrapper = $("<div class='d-flex align-items-center mb-1'></div>");
	const control_wrapper = $("<div class='flex-grow-1'></div>");
	const remove = $(
		"<button class='btn btn-xs btn-default ml-2'><i class='fa fa-trash text-danger'></i></button>"
	);
	wrapper.append(control_wrapper).append(remove);
	list.append(wrapper);

	const control = frappe.ui.form.make_control({
		df: {
			fieldtype: "Link",
			options: "Purchase Order",
			placeholder: __("Search Purchase Order"),
			get_query: () => ({
				query: "subamaz.subamaz.doctype.expense.queries.get_purchase_orders_search",
				filters: { company },
			}),
			onchange() {
				const name = this.get_value();
				if (!name) return;
				const duplicate = dialog._po_controls.some(
					(entry) => entry.control !== this && entry.control.get_value() === name
				);
				if (duplicate) {
					frappe.msgprint(__("Purchase Order {0} already added.", [name]));
					this.set_value("");
				}
			},
		},
		parent: control_wrapper,
		render_input: true,
	});
	control.refresh();
	if (value) control.set_value(value);

	const entry = { wrapper, control };
	dialog._po_controls.push(entry);
	remove.on("click", () => {
		dialog._po_controls = dialog._po_controls.filter((item) => item !== entry);
		wrapper.remove();
	});
}

function clear_po_controls(dialog) {
	dialog._po_controls.forEach((entry) => entry.wrapper.remove());
	dialog._po_controls = [];
}

function po_names(dialog) {
	return dialog._po_controls.map((entry) => entry.control.get_value()).filter(Boolean);
}

function toggle_field(dialog, fieldname, show) {
	const field = dialog.fields_dict[fieldname];
	if (field) field.$wrapper.toggle(Boolean(show));
}

function submit_all(dialog, listview) {
	const rows = dialog._rows || [];
	if (!rows.length) {
		frappe.msgprint(__("Add at least one expense."));
		return;
	}
	frappe.confirm(
		__("Submit <b>{0}</b> expense(s)?", [rows.length]),
		() => {
			dialog.hide();
			submit_sequentially(rows, listview);
		}
	);
}

function submit_sequentially(rows, listview) {
	const company = frappe.defaults.get_user_default("Company");
	const results = { success: [], failed: [] };
	const progress = new frappe.ui.Dialog({
		title: __("Submitting Expenses"),
		fields: [{ fieldtype: "HTML", fieldname: "progress_html" }],
	});
	progress.show();
	progress.get_close_btn().hide();

	const next = (index) => {
		if (index >= rows.length) {
			progress.hide();
			show_results(results, listview);
			return;
		}
		progress.fields_dict.progress_html.$wrapper.html(
			`<p>${__("Processing {0} of {1}", [index + 1, rows.length])}</p>`
		);
		const row = rows[index];
		const payload = { doctype: "Expense", company, ...row };
		frappe
			.call({ method: "frappe.client.insert", args: { doc: payload } })
			.then((inserted) => {
				if (!inserted.message) throw new Error(__("Failed to create expense"));
				return frappe.call({
					method: "frappe.client.submit",
					args: { doc: inserted.message },
				});
			})
			.then((submitted) => {
				results.success.push(submitted.message.name);
				next(index + 1);
			})
			.catch((error) => {
				results.failed.push({
					row,
					message: error.message || String(error),
				});
				next(index + 1);
			});
	};
	next(0);
}

function show_results(results, listview) {
	const success = results.success.length;
	const failed = results.failed.length;
	let html = "";
	if (success) {
		html += `<div class="alert alert-success">${__("{0} expense(s) submitted.", [
			success,
		])}</div>`;
	}
	if (failed) {
		html += `<div class="alert alert-danger">${__("{0} expense(s) failed.", [failed])}</div>`;
		html += "<ul>";
		results.failed.forEach((item) => {
			html += `<li><b>${esc(item.row.expense_description)}</b>: ${esc(item.message)}</li>`;
		});
		html += "</ul>";
	}
	const result_dialog = new frappe.ui.Dialog({
		title: __("Bulk Expense Results"),
		fields: [{ fieldtype: "HTML", fieldname: "result_html" }],
		primary_action_label: __("Close"),
		primary_action() {
			result_dialog.hide();
			listview.refresh();
		},
	});
	result_dialog.fields_dict.result_html.$wrapper.html(html);
	result_dialog.show();
}

function esc(value) {
	return frappe.utils.escape_html(value || "");
}
