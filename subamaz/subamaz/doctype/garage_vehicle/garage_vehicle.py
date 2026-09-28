import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, has_common


class GarageVehicle(Document):
	def validate(self):
		self.validate_mileage()
		self.validate_year()
		self.validate_model_make()

	def validate_year(self):
		if self.year in (None, ""):
			return
		top = getdate().year + 1
		if not 1900 <= int(self.year) <= top:
			frappe.throw(_("Year must be between 1900 and {0}").format(top))

	def validate_model_make(self):
		if self.model and not self.make:
			self.make = frappe.db.get_value("Vehicle Model", self.model, "make")
		if self.model and self.make:
			model_make = frappe.db.get_value("Vehicle Model", self.model, "make")
			if model_make and model_make != self.make:
				frappe.throw(
					_("Model {0} belongs to Make {1}, not {2}").format(
						frappe.bold(self.model), frappe.bold(model_make), frappe.bold(self.make)
					)
				)

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
