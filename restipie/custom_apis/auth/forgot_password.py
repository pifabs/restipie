import json
from datetime import datetime, timedelta

import frappe

from restipie.custom_api_core import request
from restipie.custom_api_core import response
from restipie.custom_api_core.middleware import authenticate, validate_schema

from .schema import password_reset_request_schema
from . import service


@request.api("POST", "/v1/api/request-password-reset", middlewares=(validate_schema(password_reset_request_schema),))
def reset_password(*args, **kwargs):
	try:
		result = service.handle_pwd_reset_request(**kwargs.get("data"))
		return  response.JSONResponse(**result)
	except Exception as e:
		raise e
