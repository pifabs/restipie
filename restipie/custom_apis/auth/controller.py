import frappe

from restipie.custom_api_core import request
from restipie.custom_api_core import response
from restipie.custom_api_core.middleware import authenticate, validate_schema

from .schema import (
	signup_schema,
	simple_login_schema,
	change_password_schema,
	password_reset_request_schema
)
from . import service


MIDDLEWARES = {
	"signup": (validate_schema(signup_schema),),
	"login": (validate_schema(simple_login_schema),),
	"change_password": (authenticate, validate_schema(change_password_schema),),
	"reset_password": (validate_schema(password_reset_request_schema),),
	"logout": (authenticate,)
}


@request.api("POST", "/v1/api/signup", middlewares=MIDDLEWARES["signup"])
def signup(*args, **kwargs):
	try:
		data = kwargs.get("data")
		user = service.create_account(**data)
		data["_id"] = user._id

		return response.JSONResponse(
			status_code=201,
			message="Successfully created account!",
			data=data
		)
	except Exception as e:
		raise e


@request.api("POST", "/v1/api/login", middlewares=MIDDLEWARES["login"])
def login(*args, **kwargs):
	# todo validate number of allowed sessions
	user = service.simple_login(data=kwargs.get("data"))
	return  response.JSONResponse(message="Login success!", data=user)


@request.api("PATCH", "/v1/api/users/password", middlewares=MIDDLEWARES["change_password"])
def change_password(*args, **kwargs):
	try:
		result = service.change_password(**kwargs)
		return  response.JSONResponse(**result)
	except Exception as e:
		raise e


@request.api("POST", "/v1/api/request-password-reset", middlewares=MIDDLEWARES["reset_password"])
def reset_password(*args, **kwargs):
	try:
		result = service.handle_pwd_reset_request(**kwargs.get("data"))
		return  response.JSONResponse(**result)
	except Exception as e:
		raise e


@request.api("DELETE", "/v1/api/logout", middlewares=MIDDLEWARES["logout"])
def logout(*args, **kwargs):
	try:
		service.logout(**kwargs)

		return response.JSONResponse(
			status_code=200,
			message="Logged out successfully!",
			data={}
		)
	except Exception as e:
		raise e
