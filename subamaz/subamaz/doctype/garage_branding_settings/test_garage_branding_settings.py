from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from subamaz.api.branding import get_garage_abbr


class TestGarageBrandingSettings(IntegrationTestCase):
	def test_login_context_injects_branding_and_abbr(self):
		from subamaz.www.login import get_context

		frappe.db.set_single_value("Garage Branding Settings", "garage_name", "SubaMaz")
		context = frappe._dict()
		with patch("frappe.www.login.get_context") as mock_orig:
			get_context(context)
		mock_orig.assert_called_once()
		self.assertEqual(context.abbr, "SM")
		self.assertEqual(context.branding.garage_name, "SubaMaz")

	def test_get_garage_abbr_uses_company_abbr(self):
		frappe.db.set_single_value("Garage Branding Settings", "garage_name", "SubaMaz")
		self.assertEqual(get_garage_abbr(), "SM")

	def test_get_garage_abbr_derived_from_name(self):
		frappe.db.set_single_value("Garage Branding Settings", "garage_name", "SubaMaz Garage")
		self.assertEqual(get_garage_abbr(), "SG")

	def test_permissions_system_manager(self):
		meta = frappe.get_meta("Garage Branding Settings")
		roles = {p.role: p for p in meta.permissions}
		for role in ("System Manager", "Administrator"):
			self.assertIn(role, roles)
			self.assertTrue(roles[role].read)
			self.assertTrue(roles[role].write)
