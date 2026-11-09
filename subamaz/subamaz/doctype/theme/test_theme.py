import pathlib
from unittest.mock import patch

import frappe

from subamaz.api import CACHE_KEY, DEFAULTS, _lighten, get_theme
from subamaz.testing import SubamazTestCase

# snake_case fieldname -> camelCase token exposed by get_theme()
EXPECTED_TOKENS = {
	"primary_color": "primaryColor",
	"primary_hover": "primaryHover",
	"accent_color": "accentColor",
	"danger_color": "dangerColor",
	"danger_hover": "dangerHover",
	"sidebar_background": "sidebarBg",
	"sidebar_text_color": "sidebarText",
	"active_item_background": "sidebarActiveItemBg",
	"active_item_text": "sidebarActiveText",
	"navbar_background": "navbarBg",
	"navbar_text_color": "navbarText",
	"navbar_icon_color": "navbarIcon",
	"page_head_bg": "pageHeadBg",
	"page_head_text": "pageHeadText",
	"table_header_bg": "tableHeaderBg",
	"table_header_text": "tableHeaderText",
	"even_row_bg": "tableEvenBg",
	"table_row_hover_bg": "tableRowHoverBg",
	"selectdropdown_row_hover_bg": "selectRowHoverBg",
	"primary_button_bg": "btnPrimaryBg",
	"primary_button_hover": "btnPrimaryHover",
	"primary_button_text": "btnPrimaryText",
	"danger_button_bg": "btnDangerBg",
	"danger_button_hover": "btnDangerHover",
}


class TestTheme(SubamazTestCase):
	def setUp(self):
		super().setUp()
		frappe.cache().delete_value(CACHE_KEY)

	def _empty_theme_single(self):
		frappe.db.sql("DELETE FROM `tabSingles` WHERE `doctype` = 'Theme'")

	def test_get_theme_returns_defaults(self):
		self._empty_theme_single()
		config = get_theme()
		for fieldname, token in EXPECTED_TOKENS.items():
			self.assertEqual(config[token], DEFAULTS[fieldname], f"{token} should carry the default")

	def test_get_theme_merges_saved_over_defaults(self):
		self._empty_theme_single()
		frappe.db.set_single_value("Theme", "primary_color", "1A1A1A")
		frappe.db.set_single_value("Theme", "accent_color", "FFFFFF")
		config = get_theme()
		self.assertEqual(config["primaryColor"], "#1A1A1A")
		self.assertEqual(config["accentColor"], "#FFFFFF")
		# light surfaces now fallback to lightened primary when empty
		self.assertEqual(config["tableEvenBg"], _lighten("#1A1A1A", 0.92))
		self.assertEqual(config["tableRowHoverBg"], _lighten("#1A1A1A", 0.88))
		# explicit value still wins over fallback
		frappe.db.set_single_value("Theme", "even_row_bg", "#ABCDEF")
		frappe.cache().delete_value(CACHE_KEY)
		config2 = get_theme()
		self.assertEqual(config2["tableEvenBg"], "#ABCDEF")

	def test_on_update_invalidates_cache_and_publishes(self):
		self._empty_theme_single()
		get_theme()
		self.assertIsNotNone(frappe.cache().get_value(CACHE_KEY))
		with patch("frappe.publish_realtime") as mock_publish:
			frappe.get_doc("Theme").on_update()
		self.assertIsNone(frappe.cache().get_value(CACHE_KEY))
		mock_publish.assert_called_once_with("app_theme_updated", message={"reload": True})

	def test_reset_to_defaults(self):
		frappe.db.set_single_value("Theme", "primary_color", "#FF0000")
		get_theme()
		theme = frappe.get_doc("Theme")
		with patch("frappe.publish_realtime"):
			theme.reset_to_defaults()
		for fieldname, value in DEFAULTS.items():
			self.assertEqual(theme.get(fieldname), value, f"{fieldname} should be reset")
		self.assertIsNone(frappe.cache().get_value(CACHE_KEY))

	def test_lighten_helper(self):
		self.assertEqual(_lighten("#434868", 0.92), "#F0F0F3")
		self.assertEqual(_lighten("#434868", 0.88), "#E8E9ED")
		self.assertEqual(_lighten("#000000", 1.0), "#FFFFFF")
		self.assertEqual(_lighten("#FFFFFF", 0.5), "#FFFFFF")

	def test_lighter_fallback_tracks_primary(self):
		self._empty_theme_single()
		frappe.db.set_single_value("Theme", "primary_color", "#FF0000")
		frappe.cache().delete_value(CACHE_KEY)
		config = get_theme()
		self.assertEqual(config["pageHeadBg"], _lighten("#FF0000", 0.92))
		self.assertEqual(config["selectRowHoverBg"], _lighten("#FF0000", 0.88))

	def test_sidebar_defaults_are_primary_driven(self):
		self.assertEqual(DEFAULTS["sidebar_background"], DEFAULTS["primary_color"])
		self.assertEqual(DEFAULTS["sidebar_text_color"], "#FFFFFF")
		self.assertEqual(DEFAULTS["active_item_background"], "#FFFFFF")
		self.assertEqual(DEFAULTS["active_item_text"], DEFAULTS["primary_color"])
		self.assertEqual(DEFAULTS["page_head_bg"], DEFAULTS["even_row_bg"])

	def test_defaults_are_navy_white(self):
		self.assertEqual(DEFAULTS["primary_color"], "#1A2E72")
		self.assertEqual(DEFAULTS["primary_hover"], "#14245C")
		self.assertEqual(DEFAULTS["accent_color"], "#FFFFFF")
		self.assertEqual(DEFAULTS["page_head_bg"], "#E8EEF8")
		self.assertEqual(DEFAULTS["even_row_bg"], "#E8EEF8")
		self.assertEqual(DEFAULTS["table_row_hover_bg"], "#D9E4F5")
		self.assertEqual(DEFAULTS["selectdropdown_row_hover_bg"], "#D9E4F5")

	def test_theme_sources_have_no_legacy_gold(self):
		root = pathlib.Path(frappe.get_app_path("subamaz"))
		for relative in (
			"public/css/theme.css",
			"public/js/theme.js",
			"www/login.html",
			"templates/includes/booking_form.html",
		):
			source = (root / relative).read_text()
			self.assertNotIn("#C9A227", source, f"{relative} should not contain legacy gold")

	def test_permissions_system_manager(self):
		meta = frappe.get_meta("Theme")
		roles = {p.role: p for p in meta.permissions}
		for role in ("System Manager", "Administrator"):
			self.assertIn(role, roles)
			self.assertTrue(roles[role].read)
			self.assertTrue(roles[role].write)
