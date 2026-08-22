from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.api import CACHE_KEY, DEFAULTS, get_theme

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


class TestTheme(IntegrationTestCase):
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
		frappe.db.set_single_value("Theme", "primary_color", "1A1A1A")
		frappe.db.set_single_value("Theme", "accent_color", "FFFFFF")
		config = get_theme()
		self.assertEqual(config["primaryColor"], "#1A1A1A")
		self.assertEqual(config["accentColor"], "#FFFFFF")
		self.assertEqual(config["tableEvenBg"], DEFAULTS["even_row_bg"])

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

	def test_permissions_system_manager(self):
		meta = frappe.get_meta("Theme")
		roles = {p.role: p for p in meta.permissions}
		for role in ("System Manager", "Administrator"):
			self.assertIn(role, roles)
			self.assertTrue(roles[role].read)
			self.assertTrue(roles[role].write)
