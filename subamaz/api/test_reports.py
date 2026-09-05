# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, nowdate

from subamaz.testing import ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()

from subamaz.api.reports import (
	get_money_in_breakdown,
	get_overview_stats,
	get_receivables_aging,
	get_revenue_trend,
	run_report,
)


class TestReportsAPI(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		# ensure reports/workspace exist (seeded in previous phase)
		from subamaz.api.reports import ensure_garage_reports, ensure_garage_workspace

		ensure_garage_reports()
		ensure_garage_workspace()

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.rpt_{frappe.generate_hash(length=4)}@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role,
					"send_welcome_email": 0,
					"user_type": "System User",
					"roles": [{"role": role}],
				}
			)
			user.insert(ignore_permissions=True)
		return email

	def _create_manager_user(self):
		return self._create_user("Garage Manager")

	def _create_technician_user(self):
		return self._create_user("Garage Technician")

	def test_run_report_returns_rows_and_columns(self):
		user = self._create_manager_user()
		frappe.set_user(user)
		try:
			result = run_report("Revenue by Month", filters={})
			self.assertIn("columns", result)
			self.assertIn("result", result)
			self.assertTrue(isinstance(result["columns"], list))
		finally:
			frappe.set_user("Administrator")

	def test_run_report_unknown_raises(self):
		user = self._create_manager_user()
		frappe.set_user(user)
		try:
			self.assertRaises(frappe.ValidationError, run_report, "Nonexistent Report XYZ", {})
		finally:
			frappe.set_user("Administrator")

	def test_run_report_all_twelve_exist(self):
		user = self._create_manager_user()
		frappe.set_user(user)
		try:
			names = [
				"Job Turnaround Time",
				"Jobs Completed",
				"Technician Productivity",
				"Repairs by Type",
				"Parts Usage",
				"Slow Moving Parts",
				"Stock Count Variance",
				"Stock Transfers",
				"Revenue by Month",
				"Payment Summary",
				"Outstanding Receivables",
				"Customer Statement Summary",
			]
			for name in names:
				result = run_report(name, filters={})
				self.assertIn("columns", result, f"{name} missing columns")
		finally:
			frappe.set_user("Administrator")

	def test_capability_scoping_denied_without_insights(self):
		# Technician has module:insights (per ROLE_CEILING) so need a role without insights
		# Garage Accountant has no ceiling entry — use it as denied user
		if not frappe.db.exists("Role", "Garage Accountant"):
			# fallback: use a role not in ceiling - create a user with no garage role
			email = f"test.norole.rpt_{frappe.generate_hash(length=4)}@example.com"
			if not frappe.db.exists("User", email):
				user = frappe.get_doc(
					{
						"doctype": "User",
						"email": email,
						"first_name": "NoRole",
						"send_welcome_email": 0,
						"user_type": "System User",
						"roles": [{"role": "Garage Accountant"}],
					}
				)
				user.insert(ignore_permissions=True)
			frappe.set_user(email)
			try:
				self.assertRaises(frappe.PermissionError, get_overview_stats, from_date=nowdate(), to_date=nowdate())
			finally:
				frappe.set_user("Administrator")
			return
		email = f"test.accountant.rpt_{frappe.generate_hash(length=4)}@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Accountant",
					"send_welcome_email": 0,
					"user_type": "System User",
					"roles": [{"role": "Garage Accountant"}],
				}
			)
			user.insert(ignore_permissions=True)
		frappe.set_user(email)
		try:
			self.assertRaises(frappe.PermissionError, get_overview_stats)
			self.assertRaises(frappe.PermissionError, get_revenue_trend)
			self.assertRaises(frappe.PermissionError, get_money_in_breakdown)
			self.assertRaises(frappe.PermissionError, get_receivables_aging)
			self.assertRaises(frappe.PermissionError, run_report, "Revenue by Month", {})
		finally:
			frappe.set_user("Administrator")

	def test_capability_allowed_with_insights(self):
		user = self._create_manager_user()
		frappe.set_user(user)
		try:
			# Should not throw
			result = get_overview_stats()
			self.assertIn("jobs_completed", result)
			trend = get_revenue_trend()
			self.assertIn("series", trend)
			breakdown = get_money_in_breakdown()
			self.assertIn("breakdown", breakdown)
			aging = get_receivables_aging()
			self.assertIn("buckets", aging)
		finally:
			frappe.set_user("Administrator")
