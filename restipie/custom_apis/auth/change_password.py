import frappe

from restipie.custom_api_core import request
from restipie.custom_api_core import response
from restipie.custom_api_core.middleware import authenticate, validate_schema

from .schema import change_password_schema
from . import service


@request.api("PATCH", "/v1/api/users/password", middlewares=(authenticate, validate_schema(change_password_schema),))
def change_password(*args, **kwargs):
	try:
		result = service.change_password(**kwargs)
		return  response.JSONResponse(**result)
	except Exception as e:
		raise e
