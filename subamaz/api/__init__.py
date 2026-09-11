import frappe

CACHE_KEY = "app_desk_theme"

DEFAULTS = {
	"primary_color":                 "#434868",
	"primary_hover":                 "#343753",
	"danger_color":                  "#DC2626",
	"danger_hover":                  "#B91C1C",
	"accent_color":                  "#C9A227",
	"sidebar_background":            "#434868",
	"sidebar_text_color":            "#FFFFFF",
	"active_item_background":        "#FFFFFF",
	"active_item_text":              "#434868",
	"navbar_background":             "#434868",
	"navbar_text_color":             "#FFFFFF",
	"navbar_icon_color":             "#FFFFFF",
	"page_head_bg":                  "#F0F0F3",
	"page_head_text":                "#1A1A1A",
	"table_header_bg":               "#434868",
	"table_header_text":             "#FFFFFF",
	"even_row_bg":                   "#F0F0F3",
	"table_row_hover_bg":            "#E8E9ED",
	"selectdropdown_row_hover_bg":   "#E8E9ED",
	"primary_button_bg":             "#434868",
	"primary_button_hover":          "#343753",
	"primary_button_text":           "#FFFFFF",
	"danger_button_bg":              "#DC2626",
	"danger_button_hover":           "#B91C1C",
}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_theme():
	cached = frappe.cache().get_value(CACHE_KEY)
	if cached:
		return cached

	saved = frappe.db.get_singles_dict("Theme") or {}
	config = _build_config(saved)
	frappe.cache().set_value(CACHE_KEY, config, expires_in_sec=86400)
	return config


def _sanitize_color(value):
	if not value:
		return value
	value = value.strip()
	if value and not value.startswith("#"):
		return f"#{value}"
	return value


def _lighten(hex_color, pct):
	"""Mix hex_color with white by pct (0-1). e.g. 0.92 = 92% white."""
	try:
		hex_color = hex_color.strip().lstrip("#")
		if len(hex_color) == 3:
			hex_color = "".join(c * 2 for c in hex_color)
		r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
		nr = round(r + (255 - r) * pct)
		ng = round(g + (255 - g) * pct)
		nb = round(b + (255 - b) * pct)
		return f"#{nr:02X}{ng:02X}{nb:02X}"
	except Exception:
		return hex_color


def _build_config(saved):
	# Resolve primary once for lighter fallbacks.
	_primary_raw = saved.get("primary_color") or DEFAULTS.get("primary_color", "")
	_primary = _sanitize_color(_primary_raw) or DEFAULTS["primary_color"]

	def v(fieldname):
		raw = saved.get(fieldname)
		# Fallback to computed lighter for light surfaces when field is empty.
		if not raw:
			if fieldname in ("page_head_bg", "even_row_bg"):
				return _lighten(_primary, 0.92)
			if fieldname in ("table_row_hover_bg", "selectdropdown_row_hover_bg"):
				return _lighten(_primary, 0.88)
			raw = DEFAULTS.get(fieldname, "")
		return _sanitize_color(raw)

	return {
		"primaryColor":        v("primary_color"),
		"primaryHover":        v("primary_hover"),
		"dangerColor":         v("danger_color"),
		"dangerHover":         v("danger_hover"),
		"accentColor":         v("accent_color"),
		"sidebarBg":           v("sidebar_background"),
		"sidebarText":         v("sidebar_text_color"),
		"sidebarActiveItemBg": v("active_item_background"),
		"sidebarActiveText":   v("active_item_text"),
		"navbarBg":            v("navbar_background"),
		"navbarText":          v("navbar_text_color"),
		"navbarIcon":          v("navbar_icon_color"),
		"pageHeadBg":          v("page_head_bg"),
		"pageHeadText":        v("page_head_text"),
		"tableHeaderBg":       v("table_header_bg"),
		"tableHeaderText":     v("table_header_text"),
		"tableEvenBg":         v("even_row_bg"),
		"tableRowHoverBg":     v("table_row_hover_bg"),
		"selectRowHoverBg":    v("selectdropdown_row_hover_bg"),
		"btnPrimaryBg":        v("primary_button_bg"),
		"btnPrimaryHover":     v("primary_button_hover"),
		"btnPrimaryText":      v("primary_button_text"),
		"btnDangerBg":         v("danger_button_bg"),
		"btnDangerHover":      v("danger_button_hover"),
	}
