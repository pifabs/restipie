import json

import frappe
from werkzeug.wrappers import Response
from frappe.utils.response import json_handler

from .base import Base


class JSONResponse(Base):
	valid_fields = ["message"]

	def __init__(self, **kwargs):
		self.status_code = kwargs.get("status_code", 200)
		self.success = kwargs.get("status", True)
		self.message = kwargs.get("message")
		if "data" in kwargs:
			self.data = kwargs.get("data")


def as_json(*args, **kwargs):
	"""constructs and formats response as json"""
	response = Response()
	if frappe.local.response.http_status_code:
		response.status_code = frappe.local.response['http_status_code']
		del frappe.local.response['http_status_code']

	response.mimetype = 'application/json'
	response.charset = 'utf-8'
	set_security_headers(response)
	set_cookie(response)
	# frappe.app.set_cors_headers(response)

	data = kwargs.get("data")
	status_code = data.get("status_code")
	if "status_code" in data:
		del data["status_code"]

	response.status_code = status_code or kwargs.get("status_code") or 200
	response.data = json.dumps(
		kwargs.get("data"),
		default=json_handler,
		separators=(',',':')
	)
	return response


def set_cookie(response):
	if hasattr(frappe.local, 'cookie_manager'):
		frappe.local.cookie_manager.set_cookie("SameSite", "Strict")


def set_security_headers(response):
	response.headers["X-Frame-Options"] = "DENY"
	response.headers["X-Content-Type-Options"] = "nosniff"
	response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
	response.headers["Cache-Control"] = "no-store"
	response.headers["Content-Security-Policy"] = "default-src https: frame-ancestors 'none'"
	response.headers["Feature-Policy"] = "'none'"
	response.headers["Referrer-Policy"] = "no-referrer"


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

	return as_json(
		data={
			"success": False,
			"context": context,
			"message": message
		},
		status_code=code)
