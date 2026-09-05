# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _
from frappe.utils import has_common

# Roles in the grid — order matches plan §7 / sidebar taxonomy
GARAGE_ROLES = [
	"Garage Reception",
	"Garage Technician",
	"Garage Inspector",
	"Garage Supervisor",
	"Garage Service Advisor",
	"Garage Manager",
]

# Single source of truth for ceiling — §7 matrix per plan 09.
# Manager has "*" (all capabilities). Supervisor has all modules except STAFF/SETUP.
ROLE_CEILING = {
	"Garage Technician": [
		"module:service",
		"module:customers_vehicles",
		"module:parts_stock",
		"module:insights",
	],
	"Garage Reception": [
		"module:service",
		"module:customers_vehicles",
		"module:records_money",
		"module:insights",
		"action:record_petty_cash",
	],
	"Garage Inspector": [
		"module:service",
		"module:customers_vehicles",
		"module:insights",
	],
	"Garage Supervisor": [
		"module:service",
		"module:customers_vehicles",
		"module:parts_stock",
		"module:procurement",
		"module:records_money",
		"module:insights",
		"action:approve_additional_part",
		"action:apply_invoice_discount",
		"action:edit_job_card_after_qa",
		"action:approve_credit_sale",
		"action:record_petty_cash",
		"action:view_all_technician_performance",
	],
	"Garage Service Advisor": [
		"module:service",
		"module:customers_vehicles",
		"module:parts_stock",
		"module:records_money",
		"module:insights",
		"action:approve_additional_part",
		"action:apply_invoice_discount",
		"action:approve_credit_sale",
		"action:record_petty_cash",
	],
	"Garage Manager": ["*"],
}

# Seed list — 8 modules + 9 actions per plan 09 8.5
DEFAULT_CAPABILITIES = [
	# Modules
	{
		"capability_key": "module:service",
		"label": "SERVICE",
		"capability_type": "Module",
		"module_group": "SERVICE",
		"default_enabled": 1,
	},
	{
		"capability_key": "module:customers_vehicles",
		"label": "CUSTOMERS & VEHICLES",
		"capability_type": "Module",
		"module_group": "CUSTOMERS & VEHICLES",
		"default_enabled": 1,
	},
	{
		"capability_key": "module:parts_stock",
		"label": "PARTS & STOCK",
		"capability_type": "Module",
		"module_group": "PARTS & STOCK",
		"default_enabled": 1,
	},
	{
		"capability_key": "module:procurement",
		"label": "PROCUREMENT",
		"capability_type": "Module",
		"module_group": "PROCUREMENT",
		"default_enabled": 1,
	},
	{
		"capability_key": "module:records_money",
		"label": "RECORDS & MONEY",
		"capability_type": "Module",
		"module_group": "RECORDS & MONEY",
		"default_enabled": 1,
	},
	{
		"capability_key": "module:staff",
		"label": "STAFF",
		"capability_type": "Module",
		"module_group": "STAFF",
		"default_enabled": 1,
	},
	{
		"capability_key": "module:insights",
		"label": "INSIGHTS",
		"capability_type": "Module",
		"module_group": "INSIGHTS",
		"default_enabled": 1,
	},
	{
		"capability_key": "module:setup",
		"label": "SETUP",
		"capability_type": "Module",
		"module_group": "SETUP",
		"default_enabled": 1,
	},
	# Actions
	{
		"capability_key": "action:approve_additional_part",
		"label": "Approve Additional Part",
		"capability_type": "Action",
		"module_group": "SERVICE",
		"default_enabled": 1,
	},
	{
		"capability_key": "action:apply_invoice_discount",
		"label": "Apply Invoice Discount",
		"capability_type": "Action",
		"module_group": "RECORDS & MONEY",
		"default_enabled": 1,
	},
	{
		"capability_key": "action:void_invoice",
		"label": "Void Invoice",
		"capability_type": "Action",
		"module_group": "RECORDS & MONEY",
		"default_enabled": 1,
	},
	{
		"capability_key": "action:edit_job_card_after_qa",
		"label": "Edit Job Card After QA",
		"capability_type": "Action",
		"module_group": "SERVICE",
		"default_enabled": 0,
	},
	{
		"capability_key": "action:approve_credit_sale",
		"label": "Approve Credit Sale",
		"capability_type": "Action",
		"module_group": "RECORDS & MONEY",
		"default_enabled": 1,
	},
	{
		"capability_key": "action:record_petty_cash",
		"label": "Record Petty Cash",
		"capability_type": "Action",
		"module_group": "RECORDS & MONEY",
		"default_enabled": 1,
	},
	{
		"capability_key": "action:manage_staff",
		"label": "Manage Staff",
		"capability_type": "Action",
		"module_group": "STAFF",
		"default_enabled": 1,
	},
	{
		"capability_key": "action:change_settings",
		"label": "Change Settings",
		"capability_type": "Action",
		"module_group": "SETUP",
		"default_enabled": 1,
	},
	{
		"capability_key": "action:view_all_technician_performance",
		"label": "View All Technician Performance",
		"capability_type": "Action",
		"module_group": "STAFF",
		"default_enabled": 1,
	},
]


def _is_in_ceiling(role, capability_key):
	ceiling = ROLE_CEILING.get(role, [])
	if "*" in ceiling:
		return True
	if capability_key in ceiling:
		return True
	if capability_key.startswith("module:") and "module:*" in ceiling:
		return True
	return False


def _ensure_capabilities():
	"""Idempotently create Capability rows from DEFAULT_CAPABILITIES."""
	if not frappe.db.exists("DocType", "Capability"):
		return
	for cap in DEFAULT_CAPABILITIES:
		if not frappe.db.exists("Capability", cap["capability_key"]):
			doc = frappe.get_doc({"doctype": "Capability", **cap})
			try:
				doc.insert(ignore_permissions=True)
			except Exception:
				# race or validate — swallow, best effort for tests
				pass


def has_capability(user, capability_key):
	"""Return True only if some role of user both allows and enables the capability."""
	if not user or user == "Guest":
		return False
	# ceiling check per role
	roles = frappe.get_roles(user)
	if not roles:
		return False
	_in_ceiling_any = any(_is_in_ceiling(role, capability_key) for role in roles)
	if not _in_ceiling_any:
		return False
	# now check Role Capability enabled per role in ceiling
	for role in roles:
		if not _is_in_ceiling(role, capability_key):
			continue
		enabled = frappe.db.get_value("Role Capability", {"role": role, "capability": capability_key}, "enabled")
		if enabled is None:
			# fallback to Capability.default_enabled when no row yet
			default = frappe.db.get_value("Capability", capability_key, "default_enabled")
			if default is None:
				# use DEFAULT_CAPABILITIES fallback when DocType not yet migrated in test env
				for cap in DEFAULT_CAPABILITIES:
					if cap["capability_key"] == capability_key:
						default = cap["default_enabled"]
						break
			if default:
				return True
			continue
		if enabled:
			return True
	return False


def _get_all_capabilities():
	_ensure_capabilities()
	if frappe.db.exists("DocType", "Capability"):
		rows = frappe.get_all(
			"Capability",
			fields=["capability_key", "label", "capability_type", "module_group", "default_enabled"],
			order_by="capability_key asc",
		)
		if rows:
			return rows
	return DEFAULT_CAPABILITIES


@frappe.whitelist()
def get_my_capabilities():
	"""Return resolved capability map for the current user (SPA boot)."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	caps = _get_all_capabilities()
	result = {}
	for cap in caps:
		key = cap["capability_key"]
		result[key] = bool(has_capability(frappe.session.user, key))
	return result


@frappe.whitelist()
def get_access_control_grid():
	"""Full role x capability matrix — Garage Manager only."""
	if not has_common(["Garage Manager"], frappe.get_roles()):
		frappe.throw(_("Only Garage Manager can view the access control grid"), frappe.PermissionError)
	caps = _get_all_capabilities()
	roles = list(ROLE_CEILING.keys())
	grid = []
	for role in roles:
		for cap in caps:
			key = cap["capability_key"]
			in_ceiling = _is_in_ceiling(role, key)
			enabled_val = frappe.db.get_value("Role Capability", {"role": role, "capability": key}, "enabled")
			if enabled_val is None:
				# default fallback when no row
				if in_ceiling:
					enabled_val = cap.get("default_enabled", 0)
				else:
					enabled_val = 0
			grid.append(
				{
					"role": role,
					"capability": key,
					"label": cap.get("label"),
					"capability_type": cap.get("capability_type"),
					"module_group": cap.get("module_group"),
					"in_ceiling": 1 if in_ceiling else 0,
					"available": 1 if in_ceiling else 0,
					"enabled": 1 if enabled_val else 0,
				}
			)
	return {"roles": roles, "capabilities": caps, "grid": grid}


@frappe.whitelist(methods=["POST"])
def save_access_control_grid(changes=None):
	"""Bulk upsert Role Capability.enabled — Garage Manager only, never outside ceiling."""
	if not has_common(["Garage Manager"], frappe.get_roles()):
		frappe.throw(_("Only Garage Manager can save the access control grid"), frappe.PermissionError)
	if isinstance(changes, str):
		changes = frappe.parse_json(changes) or []
	if not changes:
		changes = []
	changed = []
	for row in changes:
		role = row.get("role")
		capability = row.get("capability")
		enabled = 1 if row.get("enabled") else 0
		if not role or not capability:
			continue
		if not _is_in_ceiling(role, capability):
			frappe.throw(
				_("Cannot set capability {0} for role {1} — outside ceiling").format(capability, role),
				frappe.ValidationError,
			)
		# Ensure capability exists
		if not frappe.db.exists("Capability", capability):
			frappe.throw(_("Capability {0} does not exist").format(capability))
		existing = frappe.db.get_value("Role Capability", {"role": role, "capability": capability}, "name")
		if existing:
			doc = frappe.get_doc("Role Capability", existing)
			if doc.enabled != enabled:
				doc.enabled = enabled
				doc.save(ignore_permissions=True)
				changed.append({"role": role, "capability": capability, "enabled": enabled})
		else:
			doc = frappe.get_doc(
				{"doctype": "Role Capability", "role": role, "capability": capability, "enabled": enabled}
			)
			doc.insert(ignore_permissions=True)
			changed.append({"role": role, "capability": capability, "enabled": enabled})
	return {"changed": changed}
