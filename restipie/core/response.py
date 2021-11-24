import frappe
from frappe.utils.response import build_response


def handle_err(exception):
	code = message = None
	context = exception.__class__.__name__

	if hasattr(exception, "http_status_code"):
		code = exception.http_status_code
		message = str(exception)

	else:
		code = exception.code if hasattr(exception, "code") else 500
		message = exception.description if hasattr(exception, "description") \
			else str(exception)

	frappe.response["data"] = {
		"success": False,
		"context": context,
		"message": message
	}

	response = build_response("json")
	response.status_code = code
	return response

