import frappe

DOCK_APP = "erpnext"

# Dock entries hidden site-wide.
DOCK_HIDES = {
	"erpnext": {"Manufacturing", "Quality"},
	"frappe": {"Build"},
}

# Dock titles render the stored row title, which never passes through __(), so
# Translation records cannot rename them. These are applied as site-layer title
# overrides from the site language's Translation records.
DOCK_TITLE_SOURCES = {"Selling", "Buying"}

# Entries this site adds to an app's dock. Garage belongs to the subamaz app but
# should stay reachable from the ERPNext rail.
DOCK_ADDITIONS = {
	"erpnext": [
		{"link_type": "Workspace", "link_to": "Garage", "icon": "car", "title": "Garage"},
	],
}

# Desktop Icon rows removed from the Apps screen. The Framework children are
# listed explicitly: hiding a parent promotes its children to top level, so the
# whole group has to go for the tile to actually disappear. Those modules stay
# reachable from the dock.
DESKTOP_HIDES = {
	"Framework",
	"Build",
	"Frappe Builder",
	"Manufacturing",
	"Quality",
	"Data",
	"Email",
	"Users",
	"System",
	"Website",
	"Printing",
	"Automation",
	"Integrations",
}


def after_migrate():
	_sync_dock_layers()
	_sync_desktop_hides()
	from subamaz.sidebars import sync_accounts_sidebar

	sync_accounts_sidebar()


def _sync_dock_layers():
	for app, labels in DOCK_HIDES.items():
		titles = _dock_title_overrides() if app == DOCK_APP else {}
		_sync_dock_layer(app, labels, DOCK_ADDITIONS.get(app, []), titles)


def _sync_dock_layer(app, hidden_labels, additions, titles):
	from frappe.desk.doctype.dock.dock import _save_layer, get_dock

	layer = get_dock(app, user=None)
	standard = get_dock(app, standard=1) if layer is None else None
	source = layer.items if layer else (standard.items if standard else [])
	if not source:
		return

	items = [_dock_row(row) for row in source]
	changed = layer is None
	changed |= _apply_hides(items, hidden_labels)
	changed |= _apply_titles(items, titles)
	changed |= _apply_additions(items, additions)

	if changed:
		_save_layer(app, items, user=None, require_visible=False)
	if titles:
		_assert_dock_titles(app, titles)


def _dock_row(row):
	return {
		"link_type": row.link_type,
		"link_to": row.link_to,
		"url": row.url,
		"icon": row.icon,
		"title": row.title,
		"hidden": row.hidden,
		"added": row.added,
	}


def _apply_hides(items, labels):
	changed = False
	for row in items:
		if row["link_type"] == "Sidebar" and row["link_to"] in labels and not row["hidden"]:
			row["hidden"] = 1
			changed = True
	return changed


def _apply_titles(items, titles):
	changed = False
	for row in items:
		if row["link_to"] in titles and row["title"] != titles[row["link_to"]]:
			row["title"] = titles[row["link_to"]]
			changed = True
	return changed


def _apply_additions(items, additions):
	changed = False
	for addition in additions:
		existing = _find_row(items, addition)
		if existing:
			for field in ("icon", "title"):
				if not existing.get(field) and addition.get(field):
					existing[field] = addition[field]
					changed = True
			continue

		items.insert(_addition_index(items), {**addition, "url": None, "hidden": 0, "added": 1})
		changed = True
	return changed


def _find_row(items, addition):
	for row in items:
		if row["link_type"] == addition["link_type"] and row["link_to"] == addition["link_to"]:
			return row
	return None


def _addition_index(items):
	for index, row in enumerate(items):
		if row["link_to"] == "Stock":
			return index + 1
	return len(items)


def _dock_title_overrides():
	site_lang = frappe.db.get_single_value("System Settings", "language") or "en"
	rows = frappe.get_all(
		"Translation",
		filters={"language": site_lang, "source_text": ["in", sorted(DOCK_TITLE_SOURCES)]},
		fields=["source_text", "translated_text"],
	)
	return {row.source_text: row.translated_text.strip() for row in rows if (row.translated_text or "").strip()}


def _assert_dock_titles(app, titles):
	"""Re-assert title overrides with a direct write.

	The layer save path blanks any title equal to `_(base title)` as merely echoed
	back, which also swallows an override identical to a Translation record.
	"""
	from frappe.desk.doctype.dock.dock import get_dock

	layer = get_dock(app, user=None)
	if not layer:
		return

	dirty = False
	for row in layer.items:
		if row.link_to in titles and row.title != titles[row.link_to]:
			row.title = titles[row.link_to]
			dirty = True

	if dirty:
		layer.flags.ignore_permissions = True
		layer.save()


def _sync_desktop_hides():
	for label in DESKTOP_HIDES:
		rows = frappe.get_all(
			"Desktop Icon",
			filters={"label": label, "hidden": 0},
			pluck="name",
		)
		for name in rows:
			frappe.db.set_value("Desktop Icon", name, "hidden", 1, update_modified=False)

	from frappe.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache

	clear_desktop_icons_cache()
