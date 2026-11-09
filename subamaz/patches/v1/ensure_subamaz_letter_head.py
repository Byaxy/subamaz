import frappe

LETTER_HEAD = "SubaMaz Letter Head"
CUSTOM_CSS = '@import url("/assets/subamaz/css/print_formats.css");'


def execute():
	content = _template("letterhead.html")
	footer = _template("letterhead_footer.html")

	if frappe.db.exists("Letter Head", LETTER_HEAD):
		_update(content, footer)
		return

	frappe.get_doc(
		{
			"doctype": "Letter Head",
			"letter_head_name": LETTER_HEAD,
			"source": "HTML",
			"content": content,
			"footer_source": "HTML",
			"footer": footer,
			"custom_css": CUSTOM_CSS,
			"is_default": 0,
			"disabled": 0,
		}
	).insert(ignore_permissions=True)
	frappe.clear_cache(doctype="Letter Head")


def _update(content, footer):
	doc = frappe.get_doc("Letter Head", LETTER_HEAD)
	doc.source = "HTML"
	doc.content = content
	doc.footer_source = "HTML"
	doc.footer = footer
	doc.custom_css = CUSTOM_CSS
	doc.save(ignore_permissions=True)
	frappe.clear_cache(doctype="Letter Head")


def _template(name):
	return frappe.read_file(frappe.get_app_path("subamaz", "templates", "print_formats", name))
