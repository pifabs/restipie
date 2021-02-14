import ast
import json

import frappe
from werkzeug.exceptions import BadRequest, Unauthorized

from restipie.custom_api_core import router
from restipie.custom_api_core import response
from restipie.restipie import handler, importer


importer._import_all("restipie.custom_apis")


def handle_req(*args, **kwargs):
	"""main request handler"""
	try:
		endpoint, params = router.CustomRouter.get_instance().adapter_match()

		path = frappe.request.path
		form = frappe.local.request.form.to_dict()
		files = frappe.local.request.files
		method = frappe.local.request.method
		payload = frappe.local.request.get_data() or json.dumps({})
		headers = frappe.local.request.headers

		if form:
			payload = json.dumps(form).encode("utf-8")
			data = json.loads(frappe.safe_decode(payload))
		else:
			data = json.loads(frappe.safe_decode(payload))
		query_strings = dict(frappe.request.args)


		return handler.handle(
			endpoint=endpoint,
			path=path,
			method=method,
			headers=headers,
			query_strings=query_strings,
			params=params,
			data=data,
			file=files
		)
	except json.decoder.JSONDecodeError as e:
		return response.handle_err(BadRequest(str(e)))
	except frappe.exceptions.AuthenticationError as e:
		return response.handle_err(Unauthorized(str(e)))
	except (
		frappe.exceptions.DuplicateEntryError,
		frappe.exceptions.UniqueValidationError) as e:
		e = frappe.exceptions.ValidationError(str(e.args[2].args[1]))
		return response.handle_err(e)
	except Exception as e:
		print(frappe.get_traceback())
		return response.handle_err(e)
