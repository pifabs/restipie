from frappe.api import validate_auth_via_api_keys


def validate_auth_header(*args, **kwargs):
	validate_auth_via_api_keys()

	return args, kwargs
