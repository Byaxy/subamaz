import frappe

from subamaz.testing import SubamazTestCase


class TestGarageSettings(SubamazTestCase):
	def test_is_singleton(self):
		meta = frappe.get_meta("Garage Settings")
		self.assertEqual(meta.issingle, 1)
		self.assertEqual(meta.module, "Subamaz")

	def test_defaults(self):
		settings = frappe.get_single("Garage Settings")
		self.assertEqual(settings.project_duration_threshold_days, 14)
		self.assertEqual(settings.project_cost_threshold, 5000000)
		self.assertEqual(settings.enable_satisfaction_survey, 1)
		self.assertEqual(settings.reception_photo_requirements, "Front, Rear, Interior, Dashboard")

	def test_garage_manager_permission(self):
		permissions = frappe.get_meta("Garage Settings").permissions
		manager = next((p for p in permissions if p.role == "Garage Manager"), None)
		self.assertIsNotNone(manager)
		self.assertTrue(manager.read)
		self.assertTrue(manager.write)
		self.assertTrue(manager.delete)
