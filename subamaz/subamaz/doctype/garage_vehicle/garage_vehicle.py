import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, has_common


class GarageVehicle(Document):
	def validate(self):
		self.validate_mileage()

	def validate_mileage(self):
		if self.is_new():
			return
		prev = frappe.db.get_value("Garage Vehicle", self.name, "current_mileage")
		if prev and flt(self.current_mileage) < flt(prev) and not self.has_manager_role():
			frappe.throw(
				_("Current Mileage cannot be set lower than {0}").format(int(flt(prev)))
			)

	def has_manager_role(self):
		return bool(has_common(["Garage Manager"], frappe.get_roles()))
