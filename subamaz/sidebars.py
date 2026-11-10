import frappe

ACCOUNTS = "Accounts"

# Expense belongs beside Payment Entry in the Accounts shell. Expense Category is a master,
# so it sits in the Accounts Setup section next to the other accounting masters.
ACCOUNTS_SIDEBAR_ITEMS = (
	{
		"label": "Expense",
		"link_to": "Expense",
		"icon": "receipt-text",
		"after": "Payment Entry",
		"child": 0,
		"indent": 0,
	},
	{
		"label": "Expense Category",
		"link_to": "Expense Category",
		"icon": "table",
		"after": "Account Category",
		"child": 1,
		"indent": 0,
	},
)

LAYER_FIELDS = (
	"type",
	"label",
	"link_type",
	"link_to",
	"url",
	"filters",
	"icon",
	"child",
	"indent",
	"collapsible",
	"keep_closed",
	"show_arrow",
	"open_in_new_tab",
	"hidden",
	"added",
	"key",
)


def sync_accounts_sidebar():
	"""Keep Expense and Expense Category in ERPNext's Accounts shell."""
	if not frappe.db.exists("Sidebar", ACCOUNTS):
		return

	from frappe.desk.doctype.custom_sidebar.custom_sidebar import (
		_save_customization,
		get_customization,
	)

	layer = get_customization(ACCOUNTS, None)
	rows = _layer_rows(layer) if layer else _base_rows()
	changed = layer is None
	for spec in ACCOUNTS_SIDEBAR_ITEMS:
		changed = _ensure_item(rows, spec) or changed

	if changed:
		_save_customization(ACCOUNTS, rows, user=None)


def _base_rows():
	from frappe.desk.doctype.sidebar.sidebar import LINKED_IDENTITY_FIELDS, unlinked_key

	doc = frappe.get_doc("Sidebar", ACCOUNTS)
	rows = []
	for row in sorted(doc.items, key=lambda item: item.idx or 0):
		data = {field: row.get(field) for field in LINKED_IDENTITY_FIELDS}
		data.update(
			{
				"label": row.label,
				"icon": row.icon,
				"child": row.child or 0,
				"hidden": row.hidden or 0,
			}
		)
		if not (row.get("link_to") or row.get("url")):
			data["key"] = row.get("key") or unlinked_key(row)
		rows.append(data)
	return rows


def _layer_rows(layer):
	return [{field: row.get(field) for field in LAYER_FIELDS} for row in layer.sidebar_items]


def _ensure_item(rows, spec):
	existing = next((index for index, row in enumerate(rows) if _same_item(row, spec)), None)
	anchor = _anchor_index(rows, spec["after"])
	target = anchor + 1 if anchor is not None else len(rows)

	if existing is None:
		rows.insert(target, _added_item(spec))
		return True
	if existing == target:
		return False

	rows.pop(existing)
	if existing < target:
		target -= 1
	rows.insert(target, _added_item(spec))
	return True


def _anchor_index(rows, label):
	"""Find the anchor by identity, because stored references do not keep base labels."""
	from frappe.desk.doctype.sidebar.sidebar import LINKED_IDENTITY_FIELDS, unlinked_key

	anchor = next((row for row in frappe.get_doc("Sidebar", ACCOUNTS).items if row.label == label), None)
	if not anchor:
		return None
	if anchor.get("link_to") or anchor.get("url"):
		identity = tuple(anchor.get(field) for field in LINKED_IDENTITY_FIELDS)
		for index, row in enumerate(rows):
			if tuple(row.get(field) for field in LINKED_IDENTITY_FIELDS) == identity:
				return index
		return None
	key = anchor.get("key") or unlinked_key(anchor)
	return next((index for index, row in enumerate(rows) if row.get("key") == key), None)


def _same_item(row, spec):
	return row.get("link_type") == "DocType" and row.get("link_to") == spec["link_to"]


def _added_item(spec):
	return {
		"type": "Link",
		"label": spec["label"],
		"link_type": "DocType",
		"link_to": spec["link_to"],
		"icon": spec["icon"],
		"child": spec["child"],
		"indent": spec["indent"],
		"collapsible": 0,
		"keep_closed": 0,
		"show_arrow": 0,
		"open_in_new_tab": 0,
		"added": 1,
	}
