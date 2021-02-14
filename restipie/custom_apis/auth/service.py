import json

import frappe
from frappe.exceptions import ValidationError


def create_account(*args, **kwargs):
	frappe.set_user("Administrator")

	email = kwargs.get("email")
	mobile_no = kwargs.get("mobile_no")

	validate_email(email)
	validate_mobile_no(mobile_no)

	user = frappe.get_doc({
		"doctype": "User",
		"first_name":kwargs.get("fullname"),
		"location": kwargs.get("location"),
		"email": email,
		"mobile_no": mobile_no
	})

	user.append_roles("Customer")
	user.save()
	frappe.db.commit()

	return user


def validate_email(email):
	duplicates = frappe.get_list("User", filters={"name": email}, fields="name")

	if duplicates:
		raise ValidationError("{} already in used.".format(email))


def validate_mobile_no(mobile_no):
	duplicates = frappe.get_list(
		"User",
		filters={"mobile_no": mobile_no},
		fields="name"
	)

	if duplicates:
		raise ValidationError("{} already in used.".format(mobile_no))

