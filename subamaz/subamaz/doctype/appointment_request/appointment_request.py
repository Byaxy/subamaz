# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe.model.document import Document


class AppointmentRequest(Document):
	def validate(self):
		if self.phone:
			self.phone = self.phone.strip()
		if self.email:
			self.email = self.email.strip()
		if self.vehicle_registration:
			self.vehicle_registration = self.vehicle_registration.strip()
