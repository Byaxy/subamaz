app_name = "subamaz"
app_title = "Subamaz"
app_publisher = "Charles Byakutaga"
app_description = "Garage Management System built on frappe"
app_email = "charlesbyaxy@gmail.com"
app_license = "mit"

# Fixtures
# --------
# Scoped by `module` so export-fixtures only captures records owned by Subamaz.
# Role Profile / Workflow / Query Report are added by later phases that create them.
fixtures = [
	{
		"doctype": "Role",
		"filters": {
			"role_name": [
				"in",
				[
					"Garage Reception",
					"Garage Technician",
					"Garage Inspector",
					"Garage Supervisor",
					"Garage Service Advisor",
					"Garage Manager",
					"Garage Accountant",
				],
			]
		},
	},
	{"doctype": "Custom Field", "filters": {"module": "Subamaz"}},
	{"doctype": "Print Format", "filters": {"module": "Subamaz"}},
	{"doctype": "Workflow State", "filters": {"name": ["in", ["Draft", "Open", "Waiting Customer", "Waiting Parts", "In Progress", "Quality Check", "Completed", "Closed", "Cancelled", "On Hold"]]}},
	{"doctype": "Workflow", "filters": {"name": ["in", ["Service Order Workflow"]]}},
	{"doctype": "Capability"},
	{
		"doctype": "Role Capability",
		"filters": {
			"role": [
				"in",
				[
					"Garage Reception",
					"Garage Technician",
					"Garage Inspector",
					"Garage Supervisor",
					"Garage Service Advisor",
					"Garage Manager",
				],
			]
		},
	},
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "subamaz",
# 		"logo": "/assets/subamaz/logo.png",
# 		"title": "Subamaz",
# 		"route": "/subamaz",
# 		"has_permission": "subamaz.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = ["/assets/subamaz/css/theme.css"]
app_include_js = ["/assets/subamaz/js/theme.js"]

# include js, css files in header of web template
web_include_css = ["/assets/subamaz/css/theme.css"]
# web_include_js = "/assets/subamaz/js/subamaz.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "subamaz/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Sales Order": "public/js/sales_order.js",
	"Sales Invoice": "public/js/sales_invoice.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "subamaz/public/icons.svg"

# Home Pages
# ----------

# website user home page (by Role)
get_website_user_home_page = "subamaz.auth.get_website_user_home_page"

role_home_page = {
	"Garage Technician": "garage",
	"Garage Reception": "garage",
	"Garage Inspector": "garage",
	"Garage Supervisor": "garage",
	"Garage Service Advisor": "garage",
	"Garage Manager": "garage",
	"Garage Accountant": "garage",
}

# Website routes
website_route_rules = [
	{"from_route": "/portal/<path:app_path>", "to_route": "portal"},
	{"from_route": "/garage/<path:app_path>", "to_route": "garage"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "subamaz.utils.jinja_methods",
# 	"filters": "subamaz.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "subamaz.install.before_install"
# after_install = "subamaz.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "subamaz.uninstall.before_uninstall"
# after_uninstall = "subamaz.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "subamaz.utils.before_app_install"
# after_app_install = "subamaz.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "subamaz.utils.before_app_uninstall"
# after_app_uninstall = "subamaz.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "subamaz.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "subamaz.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"*": {
		"on_update": "subamaz.events.on_update",
		"on_trash": "subamaz.events.on_trash",
	},
	"Garage Job Card": {
		"on_update": "subamaz.subamaz.doctype.service_order.service_order.on_job_card_update"
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"subamaz.tasks.all"
# 	],
# 	"daily": [
# 		"subamaz.tasks.daily"
# 	],
# 	"hourly": [
# 		"subamaz.tasks.hourly"
# 	],
# 	"weekly": [
# 		"subamaz.tasks.weekly"
# 	],
# 	"monthly": [
# 		"subamaz.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "subamaz.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "subamaz.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"frappe.desk.query_report.run": "subamaz.report_customizer.run",
	"frappe.desk.query_report.export_query": "subamaz.report_customizer.export_query",
}
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "subamaz.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "subamaz.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["subamaz.auth.enforce_app_lockout"]
# after_request = ["subamaz.utils.after_request"]

# Job Events
# ----------
# before_job = ["subamaz.utils.before_job"]
# after_job = ["subamaz.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"subamaz.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

