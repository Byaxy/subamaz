import frappe

from subamaz.api.branding import get_garage_abbr


def _get_theme():
	from subamaz.api import DEFAULTS, _lighten, _sanitize_color

	saved = frappe.db.get_singles_dict("Theme") or {}
	primary_raw = saved.get("primary_color") or DEFAULTS.get("primary_color", "")
	primary = _sanitize_color(primary_raw) or DEFAULTS["primary_color"]
	theme = {}
	for fieldname, default in DEFAULTS.items():
		raw = saved.get(fieldname)
		if not raw:
			if fieldname in ("page_head_bg", "even_row_bg"):
				raw = _lighten(primary, 0.92)
			elif fieldname in ("table_row_hover_bg", "selectdropdown_row_hover_bg"):
				raw = _lighten(primary, 0.88)
			else:
				raw = default
		if isinstance(raw, str):
			raw = raw.strip()
			if raw and not raw.startswith("#"):
				raw = f"#{raw}"
		theme[fieldname] = raw
	return frappe._dict(theme)


def get_context(context):
	from frappe.www.login import get_context as original_get_context

	original_get_context(context)

	branding = frappe.get_single("Garage Branding Settings")
	context.branding = branding
	context.theme = _get_theme()
	context.abbr = get_garage_abbr()
	return context
