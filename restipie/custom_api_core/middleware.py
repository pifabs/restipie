import json

import frappe

import jwt
from jsonschema import Draft7Validator, FormatChecker, exceptions
from werkzeug.exceptions import BadRequest, Unauthorized

def authenticate(*args, **kwargs):
	token = frappe.get_request_header("Authorization")


	decoded = validate_token(token)
	validate_session(decoded.get("sid"))

	# set user only after token and session validation
	user = frappe.get_doc("User", { "email": decoded.get("user") })
	frappe.set_user(user.name)

	kwargs["decoded"] = decoded
	return args, kwargs


def validate_token(token):
	token = token.split(" ")[0] if token else None
	if not token: raise Unauthorized("Missing token")

	jwt_secret = frappe.local.conf.get('jwt_secret')
	jwt_alg = frappe.local.conf.get('jwt_alg')

	try:
		decoded = jwt.decode(
			token,
			jwt_secret,
			algorithms=[jwt_alg],
			issuer="codedisruptors",
			audience="restipieclient",
			# leeway=timedelta(seconds=30)
		)
		return decoded
	except Exception as e:
		raise Unauthorized("You are not logged in. Please log in and try again.")


def validate_session(sid):
	user_details = frappe.db.sql(
		"""select user from tabSessions where sid=%s""",
		sid,
		as_dict=True
	)
	if not user_details:
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
