import json

import frappe

from restipie.custom_api_core import request
from restipie.custom_api_core import response
from restipie.custom_api_core.middleware import authenticate, validate_schema

from .schema import signup_schema
from . import service


@request.api("POST", "/v1/api/signup", middlewares=(validate_schema(signup_schema),))
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
