# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate, nowdate

from subamaz.testing import SubamazTestCase, ignore_missing_dependency_doctypes

ignore_missing_dependency_doctypes()


class TestReportsCross(SubamazTestCase):
	def setUp(self):
		super().setUp()
		from subamaz.api.reports import ensure_garage_reports, ensure_garage_workspace

		ensure_garage_reports()
		ensure_garage_workspace()
		# Clean slate for seeded data is transaction-rolled-back, so we create fresh
		self.company = frappe.db.get_value("Company", {}, "name")
		self.company_currency = frappe.db.get_value("Company", self.company, "default_currency") or "USD"
		self.customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Rpt Cust {frappe.generate_hash(length=4)}"}
		).insert().name
		self.customer2 = frappe.get_doc(
			{"doctype": "Customer", "customer_name": f"Rpt Cust2 {frappe.generate_hash(length=4)}"}
		).insert().name
		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Rpt",
				"last_name": f"Emp {frappe.generate_hash(length=4)}",
				"company": self.company,
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert().name
		self.department = frappe.get_doc(
			{"doctype": "Garage Department", "department_name": f"RptDept {frappe.generate_hash(length=4)}"}
		).insert().name
		self.item = self._get_item()

	def _get_item(self):
		code = frappe.db.get_value("Item", {"is_stock_item": 0, "is_fixed_asset": 0}, "item_code")
		if code:
			return code
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": f"RptItem-{frappe.generate_hash(length=4)}",
				"item_name": "Rpt Item",
				"item_group": frappe.db.get_value("Item Group", {}, "name") or "All Item Groups",
				"stock_uom": frappe.db.get_value("UOM", {}, "name") or "Nos",
				"is_stock_item": 0,
			}
		).insert()
		return item.name

	def _create_user(self, role):
		email = f"test.{frappe.scrub(role)}.rptcross_{frappe.generate_hash(length=4)}@example.com"
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

	def _create_invoice(self, customer, posting_date, due_date, grand_total, outstanding=None):
		if outstanding is None:
			outstanding = grand_total
		inv = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"customer": customer,
				"company": self.company,
				"currency": self.company_currency,
				"conversion_rate": 1,
				"set_posting_time": 1,
				"posting_date": posting_date,
				"due_date": due_date,
				"items": [{"item_code": self.item, "qty": 1, "rate": grand_total, "conversion_rate": 1}],
			}
		)
		inv.insert(ignore_permissions=True)
		try:
			inv.submit()
		except Exception:
			pass
		# Ensure outstanding correct (ERPNext may compute)
		frappe.db.set_value("Sales Invoice", inv.name, "outstanding_amount", outstanding)
		frappe.db.set_value("Sales Invoice", inv.name, "status", "Overdue" if outstanding else "Paid")
		return inv

	def _create_payment(self, posting_date, mode, amount):
		# Use direct SQL to avoid ERPNext validation complexities; reports query tabPayment Entry directly
		name = f"PE-RPT-{frappe.generate_hash(length=6)}"
		try:
			frappe.db.sql(
				"""
				INSERT INTO `tabPayment Entry`
				(name, owner, creation, modified, modified_by, docstatus, company, posting_date, mode_of_payment, paid_amount, received_amount, party, party_type, payment_type, paid_from, paid_to)
				VALUES (%(name)s, 'Administrator', NOW(), NOW(), 'Administrator', 1, %(company)s, %(posting_date)s, %(mode)s, %(amount)s, %(amount)s, %(party)s, 'Customer', 'Receive', %(paid_from)s, %(paid_to)s)
				""",
				{
					"name": name,
					"company": self.company,
					"posting_date": posting_date,
					"mode": mode,
					"amount": amount,
					"party": self.customer,
					"paid_from": frappe.db.get_value("Account", {"account_type": "Receivable"}, "name")
					or frappe.db.get_value("Account", {}, "name"),
					"paid_to": frappe.db.get_value("Account", {"account_type": "Bank"}, "name")
					or frappe.db.get_value("Account", {}, "name"),
				},
			)
			return name
		except Exception:
			frappe.log_error(title="test payment create failed", message=frappe.get_traceback())
			return None

	def test_overview_stats_with_seeded_data(self):
		# Arrange data as Administrator first
		from subamaz.api.reports import get_overview_stats

		vehicle = frappe.get_doc(
			{
				"doctype": "Garage Vehicle",
				"registration_number": f"RPTO-{frappe.generate_hash(length=5)}",
				"vin": frappe.generate_hash(length=17),
				"customer": self.customer,
			}
		).insert()
		reception = frappe.get_doc(
			{
				"doctype": "Vehicle Reception",
				"customer": self.customer,
				"vehicle": vehicle.name,
				"reception_advisor": self.employee,
				"customer_complaint": "Report test",
				"terms_accepted": 1,
				"photos": [
					{"photo": "/files/front.jpg", "photo_type": "Front"},
					{"photo": "/files/rear.jpg", "photo_type": "Rear"},
					{"photo": "/files/interior.jpg", "photo_type": "Interior"},
					{"photo": "/files/dashboard.jpg", "photo_type": "Dashboard"},
				],
			}
		).insert()
		reception.submit()
		so = frappe.get_doc(
			{
				"doctype": "Service Order",
				"customer": self.customer,
				"vehicle": vehicle.name,
				"vehicle_reception": reception.name,
				"opening_date": nowdate(),
			}
		).insert()
		so.submit()
		jc = frappe.get_doc(
			{
				"doctype": "Garage Job Card",
				"service_order": so.name,
				"department": self.department,
				"lead_technician": self.employee,
				"status": "Completed",
			}
		).insert()
		jc.submit()
		# Invoices
		self._create_invoice(self.customer, nowdate(), add_days(nowdate(), 5), 2000)
		self._create_invoice(self.customer2, add_days(nowdate(), -40), add_days(nowdate(), -10), 5000, outstanding=5000)

		user = self._create_manager_user()
		frappe.set_user(user)
		try:
			# use wider window to include seeded job
			stats = get_overview_stats(from_date=add_days(nowdate(), -30), to_date=nowdate())
			self.assertIn("jobs_completed", stats)
			self.assertIn("revenue_total", stats)
			self.assertIn("active_job_cards", stats)
			self.assertIn("outstanding_invoices_total", stats)
			self.assertGreaterEqual(stats["jobs_completed"], 1)
			self.assertGreaterEqual(stats["revenue_total"], 2000)
			self.assertGreaterEqual(stats["outstanding_invoices_total"], 5000)
			# previous period % present
			self.assertIn("jobs_completed_change_pct", stats)
			self.assertIn("gross_margin_pct", stats)
		finally:
			frappe.set_user("Administrator")

	def test_trend_and_breakdown(self):
		# Arrange as Administrator
		self._create_invoice(self.customer, add_days(nowdate(), -40), add_days(nowdate(), -10), 3000)
		self._create_invoice(self.customer, nowdate(), add_days(nowdate(), 5), 1000)
		mode = frappe.db.get_value("Mode of Payment", {}, "name") or "Cash"
		self._create_payment(nowdate(), mode, 1500)
		cash_mode = frappe.db.get_value("Mode of Payment", {"name": ["!=", mode]}, "name")
		if cash_mode:
			self._create_payment(nowdate(), cash_mode, 700)

		user = self._create_manager_user()
		frappe.set_user(user)
		try:
			from subamaz.api.reports import get_money_in_breakdown, get_revenue_trend

			trend = get_revenue_trend(from_date=add_days(nowdate(), -60), to_date=nowdate())
			self.assertIn("series", trend)
			self.assertTrue(len(trend["series"]) >= 1)
			breakdown = get_money_in_breakdown(from_date=add_days(nowdate(), -7), to_date=nowdate())
			self.assertIn("breakdown", breakdown)
			total = sum(float(r["total"] or 0) for r in breakdown["breakdown"])
			self.assertGreaterEqual(total, 1500)
		finally:
			frappe.set_user("Administrator")

	def test_aging_buckets(self):
		# Arrange as Administrator
		self._create_invoice(self.customer, nowdate(), add_days(nowdate(), 10), 1000, outstanding=1000)
		self._create_invoice(self.customer, add_days(nowdate(), -50), add_days(nowdate(), -40), 2000, outstanding=2000)
		self._create_invoice(self.customer2, add_days(nowdate(), -90), add_days(nowdate(), -70), 3000, outstanding=3000)

		user = self._create_manager_user()
		frappe.set_user(user)
		try:
			from subamaz.api.reports import get_receivables_aging

			aging = get_receivables_aging()
			self.assertIn("buckets", aging)
			self.assertIn("top_customers", aging)
			buckets = aging["buckets"]
			self.assertIn("current_0_30", buckets)
			self.assertIn("over_30_60", buckets)
			self.assertIn("overdue_60_plus", buckets)
			self.assertGreaterEqual(buckets["current_0_30"], 1000)
			self.assertGreaterEqual(buckets["over_30_60"], 2000)
			self.assertGreaterEqual(buckets["overdue_60_plus"], 3000)
			# top customers
			self.assertTrue(len(aging["top_customers"]) >= 1)
		finally:
			frappe.set_user("Administrator")
