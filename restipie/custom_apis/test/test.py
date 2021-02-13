import json

from restipie.custom_api_core import request
from restipie.custom_api_core import response
from restipie.custom_api_core.middleware import authenticate, validate_schema

from .schema import user_schema

# import frappe
# from frappe.exceptions import ValidationError, DoesNotExistError

USERS_PATH = "/v1/api/test/users"
USER_BY_ID_PATH = USERS_PATH + "/<id>"


@request.api("POST", USERS_PATH, middlewares=(validate_schema(user_schema),))
def create_user(*args, **kwargs):
	try:
		data = kwargs.get("data")

			#don't bake the business logic here, put it in the service layer.

		return response.JSONResponse(
			status_code=201,
			message="Successfully created user!",
			data=kwargs.get("data")
		)
	except Exception as e:
		raise e


@request.api("GET", USERS_PATH)
def get_all_users(*args, **kwargs):
	try:
		qs = kwargs.get("query_strings")

			#don't bake the business logic here, put it in the service layer.

		return response.JSONResponse(data=[])
	except Exception as e:
		raise e


@request.api("GET", USER_BY_ID_PATH)
def get_one_user(*args, **kwargs):
	try:
		user_id = kwargs.get("params").get("id")

			#don't bake the business logic here, put it in the service layer.

		return response.JSONResponse(data={})
	except Exception as e:
		raise e


@request.api("PATCH", USER_BY_ID_PATH)
def update_user(*args, **kwargs):
	try:
		user_id = kwargs.get("params").get("id")

			#don't bake the business logic here, put it in the service layer.

		return response.JSONResponse(data={})
	except Exception as e:
		raise e


@request.api("DELETE", USER_BY_ID_PATH)
def  delete_user(*args, **kwargs):
	try:
		user_id = kwargs.get("params").get("id")

			#don't bake the business logic here, put it in the service layer.

		return response.JSONResponse(data={})
	except Exception as e:
		raise e
