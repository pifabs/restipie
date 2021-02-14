import json
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.core.doctype.user.user import (
	handle_password_test_fail,
	test_password_strength
)

from restipie.custom_api_core import request
from restipie.custom_api_core import response
from restipie.custom_api_core.middleware import authenticate, validate_schema

from .schema import simple_login_schema
from . import service


@request.api("POST", "/v1/api/login", middlewares=(validate_schema(simple_login_schema),))
def login(*args, **kwargs):
	# todo validate number of allowed sessions
	user = service.simple_login(data=kwargs.get("data"))
	return  response.JSONResponse(message="Login success!", data=user)
