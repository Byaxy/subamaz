import frappe


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
