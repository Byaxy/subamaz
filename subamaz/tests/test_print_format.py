# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestPrintFormatSandbox(IntegrationTestCase):
	def test_print_format_sandbox_allows_get_single_value(self):
		from frappe.utils.jinja import render_template

		html = render_template('{{ frappe.db.get_single_value("Garage Branding Settings", "garage_name") or "SubaMaz" }}')
		self.assertIsInstance(html, str)
		self.assertTrue(len(html) > 0)

	def test_print_format_sandbox_blocks_get_single(self):
		from frappe.utils.jinja import render_template

		with self.assertRaises(Exception):
			render_template('{{ frappe.get_single("Garage Branding Settings").garage_name }}')

	def test_print_format_sandbox_blocks_get_singles_dict(self):
		from frappe.utils.jinja import render_template

		with self.assertRaises(Exception):
			render_template('{{ frappe.db.get_singles_dict("Garage Branding Settings") }}')

	def test_branded_print_formats_use_get_single_value(self):
		import json
		import pathlib

		fixtures_path = pathlib.Path(__file__).parents[1] / "fixtures" / "print_format.json"
		data = json.loads(fixtures_path.read_text())
		for fmt in data:
			html = fmt.get("html") or ""
			self.assertIn("frappe.db.get_single_value", html, f"{fmt.get('name')} should use get_single_value")
			self.assertNotIn("frappe.get_single", html, f"{fmt.get('name')} should not use frappe.get_single")
			self.assertNotIn("get_singles_dict", html, f"{fmt.get('name')} should not use get_singles_dict")
