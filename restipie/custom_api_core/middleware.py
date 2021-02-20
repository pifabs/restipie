import json

import frappe
from frappe.exceptions import ValidationError

import jwt
from jsonschema import Draft7Validator, FormatChecker, exceptions
from werkzeug.exceptions import BadRequest, Unauthorized


def authenticate(*args, **kwargs):
	token = frappe.get_request_header("Authorization")

	decoded = validate_token(token)
	user = frappe.get_value(
		"User", {
			"email": decoded.get("user"),
			"enabled": 1
		}
	)
	if not user:
		raise ValidationError("Invalid token")

	validate_session(decoded.get("user"), decoded.get("sid"))

	kwargs["decoded"] = decoded
	return args, kwargs


def validate_token(token):
	if not token:raise Unauthorized("Missing token")
	token_parts = token.split(" ")

	if len(token_parts) != 2: raise Unauthorized("Invalid token")
	token = token_parts[1] if token else None
	if not token: raise Unauthorized("Invalid token")

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
	except Exception as e:
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


def validate_schema(schema):
	"""Schema validator factory"""
	def validator(*args, **kwargs):
		def _get_error(err):
			return {
				# "context": err.__class__.__name__,
				"message": err.message,
				"key": str(".".join(err.path)),
				"context": err.validator
			}

		try:
			v = Draft7Validator(schema, format_checker=FormatChecker())
			errors = sorted(v.iter_errors(kwargs.get("data")), key=str)

			if len(errors):
				errors = list(
					map(
						lambda err: _get_error(err),
							errors
						)
					)
				kwargs["errors"] = errors
			return args, kwargs
		except exceptions.ValidationError as v:
			rais(str(v))

	return validator
