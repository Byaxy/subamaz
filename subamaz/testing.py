import frappe
from frappe.tests import IntegrationTestCase


def ignore_missing_dependency_doctypes() -> None:
	"""Make Frappe's test-record generator skip link options whose DocType no longer exists.

	ERPNext still declares links to removed doctypes (e.g. `Payment Gateway`); the v16
	generator crashes on them while walking the dependency graph towards ERPNext masters.
	Call once at import time in any doctype test suite that links into ERPNext masters.
	"""
	import frappe.tests.utils.generators as generators

	original = generators.get_missing_records_doctypes
	if getattr(original, "_subamaz_safe", False):
		return

	def patched(doctype, visited=None):
		if not frappe.db.exists("DocType", doctype):
			return []
		return original(doctype, visited)

	patched._subamaz_safe = True
	generators.get_missing_records_doctypes = patched


# Name patterns that are always test residue (belt-and-suspenders behind the
# snapshot diff, e.g. for records committed outside the class transaction).
# Exact keeper names are excluded — Test Asset Item and the ambiguous demo
# items must survive.
TEST_RESIDUE_PATTERNS = ["_Test%", "_T-%", "T-SINV-%", "T-PINV-%", "QA %", "Portal %", "Rpt %", "Veh %", "P-%", "Stock-Reco-%", "test@%", "%@abc.com", "publicsite.%"]

TEST_RESIDUE_KEEPERS = {
	"Item": {"Test Asset Item", "Consulting", "Macbook Pro", "Photocopier", "138-CMS Shoe", "Loyal Item"},
}

# Doctypes the pattern sweep may touch. Structural masters (Company,
# Warehouse, groups, Price List, accounts, departments, templates) are
# deliberately excluded — e.g. "Test PCV Company" is the live default
# company and matches "Test %".
SWEEP_DOCTYPES = [
	"Employee",
	"Customer",
	"Supplier",
	"Contact",
	"Address",
	"Lead",
	"Item",
	"Garage Vehicle",
	"Appointment Request",
	"Vehicle Reception",
	"Service Order",
	"Vehicle Inspection",
	"Garage Job Card",
	"Service Timeline Entry",
	"Vehicle Delivery",
	"Petty Cash Log",
	"Material Request",
	"Supplier Quotation",
	"Quotation",
	"Sales Order",
	"Delivery Note",
	"Purchase Order",
	"Purchase Receipt",
	"Purchase Invoice",
	"Sales Invoice",
	"Payment Entry",
	"Journal Entry",
	"Stock Entry",
	"Role Capability",
	"Capability",
	"User",
]

# Doctypes the suite snapshot watches, in creation order (masters first).
# Cleanup deletes in reverse, so dependents go before the masters they link.
TRACKED_DOCTYPES = [
	"Company",
	"Warehouse",
	"UOM",
	"Item Group",
	"Customer Group",
	"Territory",
	"Supplier Group",
	"Price List",
	"Mode of Payment",
	"Cost Center",
	"Account",
	"Employee",
	"Customer",
	"Supplier",
	"Contact",
	"Address",
	"Lead",
	"Item",
	"Item Price",
	"Garage Department",
	"Service Checklist Template",
	"Garage Vehicle",
	"Appointment Request",
	"Vehicle Reception",
	"Service Order",
	"Vehicle Inspection",
	"Garage Job Card",
	"Service Timeline Entry",
	"Vehicle Delivery",
	"Petty Cash Log",
	"Material Request",
	"Supplier Quotation",
	"Quotation",
	"Sales Order",
	"Delivery Note",
	"Purchase Order",
	"Purchase Receipt",
	"Purchase Invoice",
	"Sales Invoice",
	"Payment Entry",
	"Journal Entry",
	"Stock Entry",
	"Role Capability",
	"Capability",
	"User",
]


class SubamazTestCase(IntegrationTestCase):
	"""Base for all subamaz suites: deletes generator-committed records.

	`IntegrationTestCase.setUpClass` builds test-record dependencies via
	`make_test_records` and then `frappe.db.commit()`s them, so they survive
	the per-test rollback and pollute the dev site (`_Test*`, `_T-*` residue).
	We snapshot tracked tables before setup and delete everything created
	during the class run in `tearDownClass`, so suites leave no trace.
	"""

	@classmethod
	def setUpClass(cls) -> None:
		cls._pre_test_snapshot = _snapshot_tracked()
		# Mute emails while test-record setup runs: ERPNext's import-time
		# BootStrapTestData queues welcome mail on a clean site and its
		# commit flushes the queue, which fails with no Email Account
		# configured. Cleared before tests run (some assert on sendmail).
		frappe.flags.mute_emails = True
		try:
			super().setUpClass()
		finally:
			frappe.flags.mute_emails = False

	@classmethod
	def tearDownClass(cls) -> None:
		try:
			# Roll back FIRST: per-test data accumulates in one class-level
			# transaction (IntegrationTestCase only rolls back via class
			# cleanup, which runs after this). Committing before rolling back
			# would persist every in-test insert — the exact pollution this
			# class exists to prevent. Generator records were committed in
			# setUpClass, so they survive the rollback and are diffed below.
			frappe.db.rollback()
			_delete_created(_snapshot_tracked(), cls._pre_test_snapshot)
		finally:
			super().tearDownClass()


def _snapshot_tracked() -> dict:
	snapshot = {}
	for dt in TRACKED_DOCTYPES:
		if frappe.db.exists("DocType", dt):
			snapshot[dt] = set(frappe.get_all(dt, pluck="name"))
	return snapshot


def _delete_created(after: dict, before: dict) -> None:
	leftovers = []
	for dt in reversed(TRACKED_DOCTYPES):
		for name in sorted(after.get(dt, set()) - before.get(dt, set())):
			_delete_one(dt, name, leftovers)
	for dt in reversed(SWEEP_DOCTYPES):
		_delete_residue(dt, leftovers)
	if leftovers:
		# Retry once: earlier deletes may have freed links.
		still_left = []
		for dt, name, _ in leftovers:
			if not frappe.db.exists(dt, name):
				continue
			try:
				frappe.delete_doc(dt, name, ignore_permissions=True, force=True)
				_purge_test_object_cache(dt, name)
			except Exception as e:
				still_left.append((dt, name, str(e)[:160]))
		leftovers = still_left
	frappe.db.commit()
	if leftovers:
		details = ", ".join(f"{dt} {name} ({msg})" for dt, name, msg in leftovers)
		raise AssertionError(f"Test-record cleanup failed, site left dirty: {details}")


def _delete_one(dt: str, name: str, leftovers: list) -> None:
	if not frappe.db.exists(dt, name):
		return
	try:
		doc = frappe.get_doc(dt, name)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc(dt, name, ignore_permissions=True, force=True)
		_purge_test_object_cache(dt, name)
	except Exception as e:
		leftovers.append((dt, name, str(e)[:160]))


def _delete_residue(dt: str, leftovers: list) -> None:
	"""Delete any test-pattern names the diff missed (e.g. records committed
	outside the class transaction), minus exact keepers."""
	if not frappe.db.exists("DocType", dt):
		return
	keepers = TEST_RESIDUE_KEEPERS.get(dt, set())
	for pat in TEST_RESIDUE_PATTERNS:
		for name in frappe.db.sql_list(f"select name from `tab{dt}` where name like %s", pat):
			if name not in keepers:
				_delete_one(dt, name, leftovers)


def _purge_test_object_cache(doctype: str, name: str) -> None:
	cached = getattr(frappe.local, "test_objects", {}).get(doctype) or []
	for record in [r for r in cached if dict(r).get("name") == name]:
		cached.remove(record)
