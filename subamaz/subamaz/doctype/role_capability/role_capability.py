# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RoleCapability(Document):
	def validate(self):
		self.validate_unique_pair()

	def validate_unique_pair(self):
		if not self.role or not self.capability:
			return
		filters = {"role": self.role, "capability": self.capability}
		if self.name:
			filters["name"] = ["!=", self.name]
		if frappe.db.exists("Role Capability", filters):
			frappe.throw(
				_("Role Capability for role {0} and capability {1} already exists").format(
					self.role, self.capability
				)
			)
