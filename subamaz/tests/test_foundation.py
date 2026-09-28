import frappe

from subamaz import auth
from subamaz.testing import SubamazTestCase

GARAGE_ROLES = [
	"Garage Reception",
	"Garage Technician",
	"Garage Inspector",
	"Garage Supervisor",
	"Garage Service Advisor",
	"Garage Manager",
	"Garage Accountant",
]


class TestFoundation(SubamazTestCase):
	def test_garage_roles_exist(self):
		for role in GARAGE_ROLES:
			self.assertTrue(frappe.db.exists("Role", role), f"Role {role} missing")

	def test_lockout_redirects_staff_to_garage(self):
		user = self._create_user("Garage Technician")
		frappe.set_user(user)
		frappe.local.request = frappe._dict(path="/app/garage")
		try:
			with self.assertRaises(frappe.Redirect):
				auth.enforce_app_lockout()
			self.assertEqual(frappe.local.flags.redirect_location, "/garage")
		finally:
			frappe.set_user("Administrator")
			frappe.local.flags.redirect_location = None

	def test_lockout_redirects_website_user_to_portal(self):
		user = self._create_website_user()
		frappe.set_user(user)
		frappe.local.request = frappe._dict(path="/app/garage")
		try:
			with self.assertRaises(frappe.Redirect):
				auth.enforce_app_lockout()
			self.assertEqual(frappe.local.flags.redirect_location, "/portal")
		finally:
			frappe.set_user("Administrator")
			frappe.local.flags.redirect_location = None

	def test_lockout_allows_system_manager(self):
		frappe.set_user("Administrator")
		frappe.local.request = frappe._dict(path="/app/garage")
		auth.enforce_app_lockout()
		frappe.local.flags.redirect_location = None

	def test_website_route_rules(self):
		from werkzeug.routing import Map, Rule

		rules = [
			Rule(r["from_route"], endpoint=r["to_route"])
			for r in frappe.get_hooks("website_route_rules")
		]
		url_map = Map(rules)
		urls = url_map.bind("")

		endpoint, _ = urls.match("/garage/dashboard")
		self.assertEqual(endpoint, "garage")

		endpoint, _ = urls.match("/portal/customer/1")
		self.assertEqual(endpoint, "portal")

	def test_role_home_page_hooks(self):
		home_pages = frappe.get_hooks("role_home_page")
		for role in GARAGE_ROLES:
			self.assertIn("garage", home_pages.get(role), f"{role} should map to garage")

	def test_system_manager_home_page_is_desk(self):
		self.assertEqual(auth.get_website_user_home_page("Administrator"), "desk")
		from frappe.website.utils import get_home_page

		frappe.set_user("Administrator")
		try:
			self.assertEqual(get_home_page(), "desk")
		finally:
			frappe.set_user("Administrator")

	def _create_website_user(self):
		email = "test.website.user@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Website User",
					"send_welcome_email": 0,
					"user_type": "Website User",
				}
			)
			user.insert(ignore_permissions=True)
		return email

	def _create_user(self, role, user_type="System User"):
		email = f"test.{frappe.scrub(role)}@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role,
					"send_welcome_email": 0,
					"user_type": user_type,
					"roles": [{"role": role}],
				}
			)
			user.insert(ignore_permissions=True)
		return email
