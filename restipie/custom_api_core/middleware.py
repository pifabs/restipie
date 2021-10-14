import re
from collections import deque

import jwt
import frappe
from frappe.api import validate_auth_via_api_keys
from jsonschema import FormatChecker, Draft7Validator, exceptions
from frappe.exceptions import ValidationError
from werkzeug.exceptions import Unauthorized

from .router import CustomRouter


def validate_auth_header(*args, **kwargs):
	method_path = f"{kwargs.get('method')}:{kwargs.get('endpoint')}"
	if method_path in CustomRouter.get_instance().get_private_urls():
		x_access_token = frappe.get_request_header("X-Access-Token")
		if not x_access_token:
			raise Unauthorized

		return authenticate(*args, **kwargs)

	authorization = frappe.get_request_header("Authorization")
	if not authorization:
		raise Unauthorized

	validate_auth()

	return args, kwargs


def validate_auth():
	if frappe.get_request_header("Authorization") is None:
		raise Unauthorized


	VALID_AUTH_PREFIX_TYPES = ['token']
	VALID_AUTH_PREFIX_STRING = ", ".join(VALID_AUTH_PREFIX_TYPES).title()

	authorization_header = frappe.get_request_header("Authorization", str()).split(" ")
	authorization_type = authorization_header[0].lower()


	if len(authorization_header) == 1:
		raise Unauthorized('Invalid Authorization headers, add a token with a prefix from one of the following: {0}.'.format(VALID_AUTH_PREFIX_STRING), frappe.InvalidAuthorizationHeader)

	if authorization_type in VALID_AUTH_PREFIX_TYPES:
		validate_auth_via_api_keys()
	else:
		raise Unauthorized('Invalid Authorization Type {0}, must be one of {1}.'.format(authorization_type, VALID_AUTH_PREFIX_STRING), frappe.InvalidAuthorizationPrefix)


def validate_csrf_token(*args, **kwargs):
	if frappe.local.request and frappe.local.request.method in ("POST", "PUT", "DELETE"):
		if not frappe.local.session:
			return
		if not frappe.local.session.data.csrf_token \
			or frappe.local.session.data.device=="mobile" \
			or frappe.conf.get('ignore_csrf', None):
			# not via boot

			return args, kwargs

	csrf_token = frappe.get_request_header("X-Frappe-CSRF-Token")
	if not csrf_token and "csrf_token" in frappe.local.form_dict:
		csrf_token = frappe.local.form_dict.csrf_token
		del frappe.local.form_dict["csrf_token"]

	if frappe.local.session.data.csrf_token != csrf_token:
		frappe.local.flags.disable_traceback = True
		frappe.throw("Invalid Request", frappe.CSRFTokenError)

	return args, kwargs


def get_user_from_token(*args, **kwargs):
	_id = kwargs.get("decoded").get("_id")
	return frappe.get_cached_doc("User", {"_id": _id, "enabled": 1})


def get_customer_from_token(*args, **kwargs):
	user = get_user_from_token(*args, **kwargs)
	return frappe.get_doc("Customer", {"user": user.name})


def authenticate(*args, **kwargs):
	token = frappe.get_request_header("X-Access-Token")

	decoded = validate_token(token)
	user = frappe.get_value(
		"User", {
			"_id": decoded.get("_id"),
			"enabled": 1
		}
	)
	if not user:
		raise ValidationError("Invalid token")

	sid = frappe.utils.password.decrypt(
		bytes(decoded.get("secret"), encoding="utf8")
	)

	validate_session(user, sid)

	kwargs["user"] = user
	kwargs["decoded"] = decoded
	return args, kwargs


def validate_token(token):
	if not token:
		raise Unauthorized("Missing token")

	token_parts = token.split(" ")
	if len(token_parts) != 1:
		raise Unauthorized("Invalid token")

	token = token_parts[0] if token else None
	if not token:
		raise Unauthorized("Invalid token")

	jwt_secret = frappe.local.conf.get('jwt_secret', "secret")
	jwt_alg = frappe.local.conf.get('jwt_alg', "HS256")
	site = frappe.local.site_path.replace("./", "")

	try:
		decoded = jwt.decode(
			token,
			jwt_secret,
			algorithms=[jwt_alg],
			issuer=site,
			audience="{}-client".format(site),
			# leeway=timedelta(seconds=30)
		)
		return decoded
	except Exception:
		raise Unauthorized("Invalid token")


def validate_session(email, sid):
	# if frappe.session.user == "Guest":
	# 	raise Unauthorized("You are not logged in. Please log in and try again.")
	session = frappe.db.sql(
		"""select user from tabSessions where user = %s and sid=%s""",
		(email, sid),
		as_dict=True
	)

	if not session:
		raise Unauthorized("You are not logged in. Please log in and try again.")

	frappe.set_user(session[0].get("user"))
	# frappe.local.login_manager.login_as(email)


def make_validation_error(message, path="", validator=""):
	return _get_error(
		exceptions.ValidationError(
			message,
			path=deque(path),
			validator=validator
		)
	)


def validate_schema(schema, obj=None, key=None):
	"""Schema validator factory"""
	def validator(*args, **kwargs):
		try:
			v = Draft7Validator(schema, format_checker=FormatChecker())
			if obj:
				data = obj
			elif key:
				data = kwargs.get(key)
			else:
				data = kwargs.get("data")

			errors = sorted(v.iter_errors(data), key=str)

			if len(errors):
				errors = list(map(lambda err: _get_error(err), errors))
				kwargs["errors"] = errors
			return args, kwargs
		except exceptions.ValidationError as v:
			raise (str(v))

	return validator


def _get_error(err):
	return {
		"message": err.message,
		"key": get_offending_key(err),
		"context": err.validator
	}


def get_offending_key(err):
	return (re.findall(r"\'.*?\'", err.message)[0].replace("'", "") or "") \
		if not len(err.path) else "".join(
				map(
					lambda part: str("[{}]".format(part) if isinstance(part, int) else part),
					err.path
				)
			)
