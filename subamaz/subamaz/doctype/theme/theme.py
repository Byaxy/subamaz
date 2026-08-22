import frappe
from frappe.model.document import Document

from subamaz.api import CACHE_KEY, DEFAULTS


class Theme(Document):

	def on_update(self):
		frappe.cache().delete_value(CACHE_KEY)
		frappe.publish_realtime("app_theme_updated", message={"reload": True})

	@frappe.whitelist()
	def reset_to_defaults(self):
		for fieldname, value in DEFAULTS.items():
			self.set(fieldname, value)
		self.save()
		frappe.cache().delete_value(CACHE_KEY)
