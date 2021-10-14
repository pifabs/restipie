import io
import ast
import json
import base64

import frappe
from werkzeug.exceptions import (
	BadRequest,
	Unauthorized,
	NotImplemented,
	InternalServerError,
)

from restipie.helper import log, _import_all
from . import base, request, response, middleware, router
from .router import CustomRouter


def init(name):
	_import_all(name)


def handle(*args, **kwargs):
	"""main request handler"""
	try:
		endpoint, params = CustomRouter.get_instance().adapter_match()

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
			try:
				data = json.loads(frappe.safe_decode(payload))
			except Exception:
				# data = io.BytesIO(base64.b64decode(payload))
				data = {}
		query_strings = dict(frappe.request.args)

		if files:
			for name, file in files.items():
				data[name] = {name:file}

		return _handle(
			endpoint=endpoint,
			path=path,
			method=method,
			headers=headers,
			query_strings=query_strings,
			params=params,
			data=data,
			files=files
		)
	except json.decoder.JSONDecodeError as e:
		log("JSONDecodeError")
		return response.handle_err(BadRequest(str(e)))
	except (frappe.exceptions.AuthenticationError, Unauthorized) as e:
		log("AuthenticationError")
		return response.handle_err(e)
	except frappe.exceptions.DuplicateEntryError as e:
		log("DuplicateEntryError")
		return response.handle_err(e)
	except (
		frappe.exceptions.UniqueValidationError) as e:
		e = frappe.exceptions.ValidationError(str(e.args[2].args[1]))
		log("ValidationError")
		return response.handle_err(e)
	except Exception as e:
		log(e.__class__.__name__)
		return response.handle_err(e)
	finally:
		frappe.auth.clear_cookies()


class NotImplementedError(NotImplemented):
	pass


def _handle(*args, **kwargs):
	mwargs, mwkwargs = middleware.validate_auth_header(*args, **kwargs)

	method = kwargs.get("method")
	endpoint = kwargs.get("endpoint")

	fn, middlewares = CustomRouter.get_instance().get_handler(method, endpoint)
	if not fn:
		raise NotImplementedError

	for mware in middlewares:
		mwargs, mwkwargs = mware(*mwargs, **mwkwargs)

		if "errors" in mwkwargs and len(mwkwargs.get("errors")):
			return response.as_json(
				status_code=417,
				data={
					"success": False,
					"context": "ValidationError",
					"errors": mwkwargs.get("errors")
				}
			)

	result = fn(*mwargs, **mwkwargs)
	return response.as_json(data=result.as_dict())
