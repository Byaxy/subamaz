# Copyright (c) 2026, SubaMaz Contributors
# See license.txt

import frappe
from frappe import _


@frappe.whitelist(methods=["GET", "POST"])
def send_document(doctype, name, channel, recipient=None):
	"""Shared Print / Email / PDF dispatch for Garage Admin.

	channel: "print" | "email" | "pdf"
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if doctype not in (
		"Garage Vehicle",
		"Vehicle Reception",
		"Vehicle Inspection",
		"Service Order",
		"Garage Job Card",
		"Vehicle Delivery",
		"Sales Invoice",
		"Quotation",
		"Purchase Order",
		"Purchase Invoice",
		"Payment Entry",
	):
		# allow any doctype with permission check instead of hard block
		if not frappe.db.exists("DocType", doctype):
			frappe.throw(_("Invalid DocType {0}").format(doctype))
	if not frappe.db.exists(doctype, name):
		frappe.throw(_("Document {0} {1} not found").format(doctype, name))
	doc = frappe.get_doc(doctype, name)
	# permission check
	if not frappe.has_permission(doctype, "read", doc):
		frappe.throw(_("Not permitted to read {0} {1}").format(doctype, name), frappe.PermissionError)

	channel = (channel or "").lower()
	if channel not in ("print", "email", "pdf"):
		frappe.throw(_("Invalid channel {0}").format(channel))

	# Resolve html via default print format
	html = None
	try:
		html = frappe.get_print(doctype, name, as_pdf=False)
	except Exception:
		html = f"<div>{doctype} {name}</div>"

	if channel == "print":
		return {"doctype": doctype, "name": name, "channel": channel, "html": html}

	if channel == "pdf":
		try:
			from frappe.utils.pdf import get_pdf

			pdf = get_pdf(html)
			frappe.local.response.filename = f"{name}.pdf"
			frappe.local.response.filecontent = pdf
			frappe.local.response.type = "pdf"
			return {"doctype": doctype, "name": name, "channel": channel, "pdf": True}
		except Exception:
			frappe.log_error(title="send_document pdf failed", message=frappe.get_traceback())
			frappe.throw(_("Failed to generate PDF"))

	if channel == "email":
		if not recipient:
			# try customer contact
			try:
				customer = getattr(doc, "customer", None)
				if customer:
					contact = frappe.db.get_value(
						"Dynamic Link",
						{"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"},
						"parent",
					)
					if contact:
						recipient = frappe.db.get_value("Contact", contact, "email_id")
			except Exception:
				pass
		if not recipient:
			frappe.throw(_("Recipient email required"))
		try:
			frappe.sendmail(
				recipients=[recipient],
				subject=f"{doctype} {name}",
				message=html,
				reference_doctype=doctype,
				reference_name=name,
			)
		except Exception:
			frappe.log_error(title="send_document email failed", message=frappe.get_traceback())
			frappe.throw(_("Failed to send email"))
		return {"doctype": doctype, "name": name, "channel": channel, "recipient": recipient}

	frappe.throw(_("Unhandled channel"))
