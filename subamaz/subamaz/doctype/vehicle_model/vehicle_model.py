# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class VehicleModel(Document):
	def validate(self):
		self.validate_unique_per_make()

	def validate_unique_per_make(self):
		if not (self.make and self.model_name):
			return
		duplicate = frappe.db.exists(
			"Vehicle Model",
			{"make": self.make, "model_name": self.model_name, "name": ["!=", self.name]},
		)
		if duplicate:
			frappe.throw(
				_("Model {0} already exists for Make {1}").format(
					frappe.bold(self.model_name), frappe.bold(self.make)
				)
			)
