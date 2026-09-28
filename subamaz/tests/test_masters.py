# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe

from subamaz.testing import SubamazTestCase

FULL = {"read": 1, "write": 1, "create": 1, "delete": 1}
READ = {"read": 1}
SUBMIT = {"read": 1, "write": 1, "create": 1, "submit": 1}

MATRIX = {
	"Vehicle Reception": {
		"Garage Reception": SUBMIT,
		"Garage Technician": READ,
		"Garage Inspector": READ,
		"Garage Supervisor": SUBMIT,
		"Garage Service Advisor": {"read": 1, "write": 1, "create": 1},
		"Garage Manager": {**FULL, "submit": 1, "cancel": 1, "amend": 1},
		"System Manager": {**FULL, "submit": 1, "cancel": 1, "amend": 1},
	},
	"Garage Vehicle": {
		"Garage Reception": {"read": 1, "write": 1},
		"Garage Technician": {"read": 1},
		"Garage Inspector": {"read": 1},
		"Garage Supervisor": {"read": 1, "write": 1},
		"Garage Service Advisor": {"read": 1, "write": 1},
		"Garage Manager": FULL,
		"System Manager": FULL,
	},
	"Garage Department": {
		"Garage Reception": {"read": 1},
		"Garage Technician": {"read": 1},
		"Garage Inspector": {"read": 1},
		"Garage Supervisor": {"read": 1},
		"Garage Service Advisor": {"read": 1},
		"Garage Manager": FULL,
		"System Manager": FULL,
	},
	"Service Checklist Template": {
		"Garage Reception": {"read": 1},
		"Garage Technician": {"read": 1},
		"Garage Inspector": {"read": 1},
		"Garage Supervisor": {"read": 1, "write": 1},
		"Garage Service Advisor": {"read": 1},
		"Garage Manager": FULL,
		"System Manager": FULL,
	},
}


class TestMasters(SubamazTestCase):
	def test_permission_matrix_rows_exist(self):
		for doctype, expected in MATRIX.items():
			meta = frappe.get_meta(doctype)
			rows = {}
			for perm in meta.permissions:
				flags = {
					k: perm.get(k)
					for k in ("read", "write", "create", "delete", "submit", "cancel", "amend")
				}
				rows.setdefault(perm.role, {}).update({k: v for k, v in flags.items() if v})
			for role, flags in expected.items():
				self.assertIn(role, rows, f"{doctype}: {role} permission row missing")
				for flag in flags:
					self.assertTrue(rows[role].get(flag), f"{doctype}: {role} lacks '{flag}'")
