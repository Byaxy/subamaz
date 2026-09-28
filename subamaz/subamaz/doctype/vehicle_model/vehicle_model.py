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
		# Names come from model_name (autoname), and set_new_name runs before
		# validate, so a new doc already carries its final name: excluding it
		# would also exclude the conflicting row and let the DB raise a raw
		# DuplicateEntryError instead of the message below.
		filters = {"make": self.make, "model_name": self.model_name}
		if not self.is_new():
			filters["name"] = ["!=", self.name]
		duplicate = frappe.db.exists("Vehicle Model", filters)
		if duplicate:
			frappe.throw(
				_("Model {0} already exists for Make {1}").format(
					frappe.bold(self.model_name), frappe.bold(self.make)
				)
			)
