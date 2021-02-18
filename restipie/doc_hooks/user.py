import frappe

def set_id(doc, method):
	doc._id = frappe.generate_hash("User", 15)
